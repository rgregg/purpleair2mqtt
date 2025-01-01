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

import logging
import os
from logging.handlers import RotatingFileHandler
from .mqtt_event_receiver import MqttConnectionClient
from .app_configuration import FileBasedAppConfig, LoggingConfiguration
from .purpleair_receiver import PurpleAirReceiver

logger = logging.getLogger(__name__)

# Main function
def main():
    """Entry point for app"""

    # Load configuration
    path = os.getenv('CONFIG_FILE', '/app/config/config.yaml')
    logger.info("Reading configuration from %s", path)
    config = FileBasedAppConfig(path)
    logger.debug("Configuration: %s", config)

    configure_logging(config.logging)

    # Create the Purple Air data receiver
    sensor_receiver = PurpleAirReceiver(config.purple_air, config.home_assistant)

    # Create the MQTT client and connect
    mqtt_client = MqttConnectionClient(config.mqtt, False, sensor_receiver)
    mqtt_client.connect_and_loop()

def configure_logging(config:LoggingConfiguration):
    """ Configure logging for the class """
    level = logging.INFO
    if config.level.upper() == "DEBUG":
        level = logging.DEBUG
    if config.level.upper() == "WARNING":
        level = logging.WARNING

    # enable logging
    logging.basicConfig(
        level=level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    if config.path is not None:
        max_keep = config.max_keep or 10
        handler = RotatingFileHandler(config.path, maxBytes=5*1024*1024, backupCount=max_keep)
        handler.setLevel(level)
        formatter = logging.Formatter("%(asctime)-15s %(name)-8s %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

if __name__ == '__main__':
    main()