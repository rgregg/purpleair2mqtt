# MIT License
# Copyright (c) 2025 Ryan Gregg
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Retrieve data from the Purple Air devices and publish it via MQTT
"""

import logging
import json
import httpx
from .app_configuration import PurpleAirConfiguration, HomeAssistantConfiguration
from .mqtt_event_receiver import MqttConnectionClient, MqttEventProcessor

logger = logging.getLogger(__name__)

class PurpleAirReceiver(MqttEventProcessor):
    """Retrieves data from the Purple Air devices and publishes it via MQTT"""
    def __init__(self, config:PurpleAirConfiguration, hass_config:HomeAssistantConfiguration):
        self.config = config
        self.hass_config = hass_config
        self.hass_discovery_complete = False

    def retrieve_latest_data(self, mqtt_client:MqttConnectionClient):
        """Retrieves the latest data from the Purple Air devices"""
        logger.info("Retrieving data from Purple Air devices")
        
        for url in self.config.urls:
            logger.info("Retrieving data from %s", url)
            # Retrieve the data from the Purple Air device
            try:
                response = httpx.get(url)
            except httpx.RequestError as exc:
                logger.error("Failed to retrieve data from %s: %s", url, exc)
                continue

            if response.status_code != 200:
                logger.error("Failed to retrieve data from %s: %s", url, response.text)
                continue

            data = response.text
            self.process_json_data(mqtt_client, data)

    def process_json_data(self, mqtt_client:MqttConnectionClient, data:str):
        """Processes the response from the PurpleAir device and publishes it via MQTT"""
        logger.debug("Processing data: %s", data)
        
        # Publish the data to the MQTT server
        sensor = json.loads(data)
       
        sensor_id = self.strip_seperators(sensor.get('SensorId'))
        mqtt_client.publish_sensor_value(sensor_id, data)


    def publish_discovery_for_devices(self, mqtt_client:MqttConnectionClient):
        """Publishes HASS discovery information for registered devices"""
        for device_url in self.config.urls:
            logger.info("Publishing discovery for %s", device_url)

            # Retrieve the data from the Purple Air device
            try:
                response = httpx.get(device_url)
            except httpx.RequestError as exc:
                logger.error("Failed to retrieve data from %s: %s", device_url, exc)
                continue
            
            if response.status_code != 200:
                logger.error("Failed to retrieve data from %s: %s", device_url, response.text)
                continue

            data = response.json()
            sensor_id = self.strip_seperators(data.get('SensorId'))
            value_topic = mqtt_client.format_sensor_topic(sensor_id)

            # create hass discovery record
            for key, _value in data.items():
                if key in self.purple_air_sensors:
                    sensor = self.purple_air_sensors[key].copy()

                    # build the specific payload for this sensor
                    sensor["availability"] = {
                            "topic": mqtt_client.config.status_topic,
                        }
                    sensor["payload_available"] = mqtt_client.ONLINE_STATUS
                    sensor["payload_not_available"] = mqtt_client.OFFLINE_STATUS
                    
                    sensor["device"] = {
                        "hw_version": data.get("hardwareversion"),
                        "identifiers": [
                            f"purpleair_{sensor_id}"
                        ],
                        "manufacturer": "PurpleAir",
                        "model": "PurpleAir Sensor",
                        "name": data.get("Geo"),
                        "sw_version": data.get("version")
                    }
                    sensor["unique_id"] = f"purpleair_{sensor_id}_{key}"
                    sensor["state_topic"] = value_topic

                    discovery_topic = f"{self.hass_config.discovery_topic}/sensor/purpleair2mqtt_{sensor_id}/{key}/config"
                    payload = json.dumps(sensor)
                    logger.debug("Publishing discovery for %s: %s", discovery_topic, payload)
                    mqtt_client.publish_message(discovery_topic, payload, retain=True)
                else:
                    logger.debug("Skipping unknown sensor key %s", key)
    
    def strip_seperators(self, value:str):
        """Strips out the separators from a string"""
        return value.replace(" ", "").replace(",", "").replace(":", "").replace("-", "")


    # Implement the abstract methods from the MqttEventProcessor

    def process_mqtt_event(self, client:MqttConnectionClient, _topic:str, _data):
        pass

    def process_mqtt_loop(self, client:MqttConnectionClient):
        """Do work during the event loop for the MQTT client"""

        if self.hass_config.discovery_enabled and not self.hass_discovery_complete:
            self.hass_discovery_complete = True
            self.publish_discovery_for_devices(client)

        self.retrieve_latest_data(client)
        return self.config.refresh_interval_seconds

    def wants_json(self, _client:MqttConnectionClient, _topic:str):
        return False
    
    def clean_up(self, _client):
        pass

    # based on information from https://community.purpleair.com/t/sensor-json-documentation/6917
    purple_air_sensors = {
        # General values
        #"SensorId": {},
        "Adc": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "AQI",
            "value_template": "{{ value_json.Adc }}",
            "name": "Air Quality Index",
            "icon": ""
        },
        "current_temp_f": {
            "device_class": "temperature",
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "°F",
            "value_template": "{{ value_json.current_temp_f }}",
            "name": "Current Temperature"
        },
        "current_humidity": {
            "device_class": "humidity",
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.current_humidity }}",
            "name": "Current Humidity"
        },
        "current_dewpoint_f": {
            "device_class": "temperature",
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "°F",
            "value_template": "{{ value_json.current_dewpoint_f }}",
            "name": "Current Dewpoint"
        },
        "pressure": {
            "device_class": "pressure",
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "mbar",
            "value_template": "{{ value_json.pressure }}",
            "name": "Air Pressure"
        },

        # B sensor values
        "p25aqic_b": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.p25aqic_b }}",
            "name": "PM2.5 AQI Color B"
        },
        "pm2.5_aqi_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "value_template": "{{ value_json.pm2.5_aqi_b }}",
            "name": "PM2.5 AQI B"
        },

        # PM readings from channel B using the CF=1 estimation of density
        "pm1_0_cf_1_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm1_0_cf_1_b }}",
            "name": "1.0um CF=1 Mass B"
        },
        "pm2_5_cf_1_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm2_5_cf_1_b }}",
            "name": "2.5um CF=1 Mass B"
        },
        "pm10_0_cf_1_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm10_0_cf_1_b }}",
            "name": "10.0um CF=1 Mass B"
        },

        # PM readings from channel B using the ATM estimation of density
        "pm1_0_atm_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm1_0_atm_b }}",
            "name": "1.0um ATM Mass B"
        },
        "pm2_5_atm_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm2_5_atm_b }}",
            "name": "2.5um ATM Mass B"
        },
        "pm10_0_atm_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm10_0_atm_b }}",
            "name": "10.0um ATM Mass B"
        },

        # Particle counts
        "p_0_3_um_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_0_3_um_b }}",
            "name": "0.3um Particle Count B"
        },
        "p_0_5_um_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_0_5_um_b }}",
            "name": "0.5um Particle Count B"
        },
        "p_1_0_um_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_1_0_um_b }}",
            "name": "1.0um Particle Count B"
        },
        "p_2_5_um_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_2_5_um_b }}",
            "name": "2.5um Particle Count B"
        },
        "p_5_0_um_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_5_0_um_b }}",
            "name": "5.0um Particle Count B"
        },
        "p_10_0_um_b": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_10_0_um_b }}",
            "name": "10.0um Particle Count B"
        },
        
        # A sensor values
        "p25aqic": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.p25aqic }}",
            "name": "PM2.5 AQI Color A"
        },
        "pm2.5_aqi": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "value_template": "{{ value_json.pm2.5_aqi }}",
            "name": "PM2.5 AQI A"
        },

        # PM readings from channel A using the CF=1 estimation of density
        "pm1_0_cf_1": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm1_0_cf_1 }}",
            "name": "1.0um CF=1 Mass A"
        },
        "pm2_5_cf_1": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm2_5_cf_1 }}",
            "name": "2.5um CF=1 Mass A"
        },
        "pm10_0_cf_1": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm10_0_cf_1 }}",
            "name": "10.0um CF=1 Mass A"
        },

        # PM readings from channel A using the ATM estimation of density
        "pm1_0_atm": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm1_0_atm }}",
            "name": "1.0um ATM Mass A"
        },
        "pm2_5_atm": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm2_5_atm }}",
            "name": "2.5um ATM Mass A"
        },
        "pm10_0_atm": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "ug/m3",
            "value_template": "{{ value_json.pm10_0_atm }}",
            "name": "10.0um ATM Mass A"
        },

        # Particle counts
        "p_0_3_um": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_0_3_um }}",
            "name": "0.3um Particle Count A"
        },
        "p_0_5_um": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_0_5_um }}",
            "name": "0.5um Particle Count A"
        },
        "p_1_0_um": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_1_0_um }}",
            "name": "1.0um Particle Count A"
        },
        "p_2_5_um": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_2_5_um }}",
            "name": "2.5um Particle Count A"
        },
        "p_5_0_um": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_5_0_um }}",
            "name": "5.0um Particle Count A"
        },
        "p_10_0_um": {
            "enabled_by_default": True,
            "state_class": "measurement",
            "unit_of_measurement": "um/dl",
            "value_template": "{{ value_json.p_10_0_um }}",
            "name": "10.0um Particle Count A"
        },

        # Diagnostic values
     
        "Geo": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "PurpleAir-{{ value_json.Geo }}",
            "name": "Name of the PurpleAir WiFi network for device setup"
        },
        "Mem": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.Mem }}",
            "name": "Free Heap Memory"
        },
        "memfrag": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.memfrag }}",
            "name": "Fragmentation of Heap Memory"
        },
        "memfb": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.memfb }}",
            "name": "Max Free Block Size"
        },
        "memcs": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.memcs }}",
            "name": "Free Stack Space"
        },
        "loggingrate": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.loggingrate }}",
            "name": "Logging Rate"
        },
        "uptime": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.uptime }}",
            "name": "Uptime"
        },
        "rssi": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.rssi }}",
            "name": "WiFi Signal Strength"
        },
        "hardwareversion": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.hardwareversion }}",
            "name": "Hardware Version"
        },
        "hardwarediscovered": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.hardwarediscovered }}",
            "name": "Hardware Discovered"
        },
        "status_0": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.status_0 }}",
            "name": "NTP time sync"
        },
        "status_1": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.status_1 }}",
            "name": "Location lookup"
        },
        "status_2": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.status_2 }}",
            "name": "Update check"
        },
        "status_3": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.status_3 }}",
            "name": "Connection to PurpleAir servers"
        },
        "status_6": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.status_6 }}",
            "name": "Data Processor #1 Status"
        },
        "ssid": {
            "enabled_by_default": False,
            "state_class": "measurement",
            "value_template": "{{ value_json.ssid }}",
            "name": "WiFi SSID"
        }
    }
