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
AppConfiguration module
This module provides classes and functions to manage the configuration of an application that integrates with an MQTT broker, PurpleAir API, and other components. It includes support for loading configuration from a YAML file.
Classes:
    MqttConfiguration: Configuration for the MQTT broker.
    PurpleAirConfiguration: Configuration for the PurpleAir API.
    LoggingConfiguration: Configuration for the logger.
    HomeAssistantConfiguration: Configuration for Home Assistant integration.
    AppConfig: Configuration for the application.
    FileBasedAppConfig: App configuration that is loaded from a file.
Functions:
    AppConfig.apply_from_dict(data): Load settings from a dictionary.
    AppConfig.load_logging_config(data): Load the logging settings.
    AppConfig.load_purple_air_config(data): Load the PurpleAir settings.
    AppConfig.load_mqtt_config(data): Load saved configuration for the MQTT.
    AppConfig.load_home_assistant_config(data): Load Home Assistant integration settings.
    FileBasedAppConfig.reload_function(): Reload the configuration from the file.
"""

import logging
from pathlib import Path
import yaml

# Define the classes to map the structure
logger = logging.getLogger(__name__)

class MqttConfiguration:
    """Configuration for the MQTT broker"""
    def __init__(self):
        self.host = "localhost"
        self.port = 1883
        self.username = None
        self.password = None
        self.listen_topic = "#"
        self.status_topic = "alerts/purpleair2mqtt"
        self.sensor_topic_root = "sensors/purpleair2mqtt"

    def __repr__(self):
        return f"Mqtt(host={self.host}, username={self.username}, password={self.password}, listen_topic={self.listen_topic}, alert_topic={self.status_topic}, sensor_topic_root={self.sensor_topic_root})"

class PurpleAirConfiguration:
    """Configuration for the PurpleAir API"""
    def __init__(self):
        self.urls = []
        self.refresh_interval_seconds = 300
   
    def __repr__(self):
        return f"PurpleAir(urls={self.urls}, refresh_interval_seconds={self.refresh_interval_seconds})"

class LoggingConfiguration:
    """Configuration for the logger"""
    def __init__(self):
        self.level = logging.INFO
        self.path = None
        self.rotate = False
        self.max_keep = 10
    
    def __repr__(self):
        return f"Logging(level={self.level}, path={self.path}, rotate={self.rotate}, max_keep={self.max_keep})"

class HomeAssistantConfiguration:
    """Configuration for Home Assistant integration"""
    def __init__(self):
        self.discovery_enabled = True
        self.discovery_topic = "homeassistant"

    def __repr__(self):
        return f"HomeAssistant(discovery_enabled={self.discovery_enabled}, discovery_topic={self.discovery_topic})"

class AppConfig:
    """Configuration for the application"""
    def __init__(self):
        self.mqtt = MqttConfiguration()
        self.purple_air = PurpleAirConfiguration()
        self.logging = LoggingConfiguration()
        self.home_assistant = HomeAssistantConfiguration()

    def apply_from_dict(self, data):
        """Load settings from a dictionary"""
        self.load_mqtt_config(data)
        self.load_purple_air_config(data)
        self.load_logging_config(data)
        self.load_home_assistant_config(data)

    def load_logging_config(self, data):
        """Load the logging settings"""
        log_config = data.get('logging')
        if log_config is not None:
            self.logging.level = log_config.get('level')
            self.logging.path = log_config.get('path')
            self.logging.rotate = log_config.get('rotate')
            self.logging.max_keep = log_config.get('max_keep')

    def load_purple_air_config(self, data):
        """Load the PurpleAir settings"""
        purple_air = data.get('purple_air')
        if purple_air is not None:
            self.purple_air.urls = purple_air.get('urls') or []
            self.purple_air.refresh_interval_seconds = purple_air.get('refresh_interval_seconds') or 300
    
    def load_mqtt_config(self, data):
        """Load saved configuration for the MQTT"""
        mqtt = data.get('mqtt')
        if mqtt is not None:
            self.mqtt.host = mqtt.get('host') or "localhost"
            self.mqtt.port = mqtt.get('port') or 1883
            self.mqtt.listen_topic = mqtt.get('listen_topic') or "#"
            self.mqtt.status_topic = mqtt.get('status_topic') or None
            self.mqtt.sensor_topic_root = mqtt.get('sensor_topic_root') or None
            self.mqtt.username = mqtt.get('username')
            self.mqtt.password = mqtt.get('password')

    def load_home_assistant_config(self, data):
        """Load Home Assistant integration settings"""
        home_assistant = data.get('home_assistant')
        if home_assistant is not None:
            self.home_assistant.discovery_enabled = home_assistant.get('discovery_enabled') or False
            self.home_assistant.discovery_topic = home_assistant.get('discovery_topic') or "homeassistant"
        
    def __repr__(self):
        return (f"AppConfig(mqtt={self.mqtt}, logging={self.logging}, home_assistant={self.home_assistant}, purple_air={self.purple_air})")

class FileBasedAppConfig(AppConfig):
    """App configuration that is loaded from a file"""
    def __init__(self, config_file):
        super().__init__()
        self.file_path = Path(config_file).resolve()
        self.reload_function()

    def reload_function(self):
        """Load the configuration from the file"""
        logger.info("Loading app configuration from %s", self.file_path)
        with open(self.file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            self.apply_from_dict(data)
