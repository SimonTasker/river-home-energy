# MQTT Imports
import paho.mqtt.client as mqtt
from datetime import datetime
import json

# Application imports
import logging

# ================================================
class MQTTRiverTrainer:
    # ================================================
    # Class Constructor
    def __init__(self, config, river_model):
        self.river_model = river_model

        # Define loggers
        self.mqtt_logger = logging.getLogger('MQTT')

        # Create MQTT Client
        self.client = mqtt.Client()
        self.client.enable_logger(logger=self.mqtt_logger)

        # Register callbacks
        self.client.on_connect=self.on_connect
        self.client.on_message=self.on_message

        # Read mqtt config items
        self.mqtt_address = config["MQTT Settings"]["Address"]
        self.mqtt_port = int(config["MQTT Settings"]["Port"])
        self.mqtt_subscription = config["MQTT Settings"]["Topic"]

    # ================================================
    # Callback from MQTT connection attempt
    def on_connect(self, client, userdata, flags, rc):
        # Only subscribe to topic if rc == 0
        if rc == 0:
            self.mqtt_logger.info("Connected and subscribing to topics")
            # Topic subscription packaged into userdata
            client.subscribe(self.mqtt_subscription)
        else:
            self.mqtt_logger.critical("Failed to connect, rc: %s", rc)

    # ================================================
    # Callback from MQTT connection attempt
    def on_message(self, client, userdata, message):
        # unpack message payload into json
        payload = message.payload.decode("utf-8")
        json_payload = json.loads(payload)

        self.mqtt_logger.debug("Received message: " + str(json_payload))

        # Format: yyyy-mm-ddTHH:MM:SS
        dt = datetime.strptime(json_payload["Time"], '%Y-%m-%dT%H:%M:%S')
        # Custom x values - derived from message payload
        x = { 'epoch' : dt.timestamp() }
        # Require y
        y = json_payload["ENERGY"]["Power"]

        # train model on payload data
        self.river_model.train(x, y)

    # ================================================
    def connect_and_start(self):
        self.mqtt_logger.debug("Starting MQTT Loop")
        # Asynchronously connect client to MQTT stream
        self.client.connect_async(self.mqtt_address, self.mqtt_port, 60)

        # Start MQTT client async loop
        self.client.loop_start()

    # ================================================
    def stop(self):
        self.mqtt_logger.info("Stopping MQTT Loop")
        # Stop MQTT client async loop
        self.client.loop_stop()
