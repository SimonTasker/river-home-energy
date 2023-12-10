# Application imports
import argparse
from configparser import ConfigParser
import logging
import sys
import asyncio
import json

from mediator import Mediator
from mqtt_client import MQTTClient 
from river_model import RiverModel
from mediator import Mediator

# ================================================
# Application Arguments
parser = argparse.ArgumentParser(
    prog='Home Energy',
    description='Connects to a Tasmota MQTT feed, learns usage, and provides predictions'
)

parser.add_argument('-c', '--configuration', dest='configuration', action='store',
                    default='configuration.ini',
                    help='Application Configuration File. (Default: configuration.ini)')

parser.add_argument('-d', '--data_dir', dest='data_dir', action='store',
                    default='/data',
                    help='Application Data Directory. (Default: /data)')

# ================================================
# Get root logger and set default level to NOTSET (we'll use handlers on the root instead)
root_logger = logging.getLogger()
root_logger.setLevel(logging.NOTSET)

# Define formatter
log_format = logging.Formatter(fmt='%(asctime)s [%(name)s] - %(levelname)s - %(message)s',
                                   datefmt='%y-%m-%d %H:%M:%S')

# ================================================
# Config Reader
def read_config(config_file):
    config = ConfigParser()
    try:
        config.read_file(open(config_file))
    except:
        raise Exception('Unable to read configuration file at ' + config_file)
    
    return config

# ================================================
# Config Logger
def print_config(config, logger):
    # Pretty-print the contents to the logger
    for section in config.sections():
        logger.info(f"   {section}")
        for key, value in config.items(section):
            logger.info(f"      {key} = {value}")

# ================================================
# Main
if __name__ == "__main__":
    # Pass CLAs
    args = parser.parse_args()

    # Extract CLA values
    data_dir = args.data_dir
    config_file = args.configuration

    try:
        config = read_config(config_file)
    except Exception as e:
        print(e)
        quit()

    # Define and add File Handler for logging
    application_name = config['App Settings']['Name'].replace(' ','_')
    file_handler = logging.FileHandler(data_dir+'/'+application_name+'.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    # Define and add Console handler for logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    config.values

    # Create "Application" level logger
    application_logger = logging.getLogger("Application")
    # First print the application configuration
    application_logger.info("Application config: ")
    print_config(config, application_logger)
    application_logger.info("Starting " + config['App Settings']['Name'])

    # Instantiate River Model
    river_model = RiverModel(data_dir, config)
    # Instantiate the Trainer
    mqtt_client = MQTTClient(config)
    # Instantiate the Mediator
    mediator = Mediator(river_model, mqtt_client)

    # Connect and start the MQTT Client
    mqtt_client.connect_and_start()

    # Get event loop
    loop = asyncio.get_event_loop()

    # Start application until stopped
    try:
        loop.run_forever()
    finally:
        mqtt_client.stop()
        loop.close()