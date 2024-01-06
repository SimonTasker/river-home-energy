# MQTT Imports
import paho.mqtt.client as mqtt
import json

# Application imports
import logging
import datetime
from mediator import MediatedComponent

# ================================================
class MQTTClient(MediatedComponent):
    # ================================================
    # Class Constructor
    def __init__(self, config):
        MediatedComponent.__init__(self)

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
        self.mqtt_subscription = config["MQTT Settings"]["Listen Topic"]
        self.mqtt_publish_topic = config["MQTT Settings"]["Publish Topic"]

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
    # Callback from MQTT when message is received
    def on_message(self, client, userdata, message):
        # unpack message payload into json
        payload = message.payload.decode("utf-8")
        json_payload = json.loads(payload)

        self.mqtt_logger.debug("Received message: " + str(json_payload))

        # Notify Mediator of new message
        self.mediator.notify_mqtt_message(json_payload)

    # ================================================
    def publish_prediction(self, x: datetime.datetime, name, y):
        # Format prediction into desired format
        data = {
            "Time": x.strftime("%Y-%m-%dT%H:%M:%S"),
            "Prediction": y
        }
        # Dump json into str
        json_data = json.dumps(data)

        # Append topic with model name
        topic = self.mqtt_publish_topic + "/" + name

        self.mqtt_logger.info("Publishing " + str(json_data) + " to " + topic)

        # Publish prediction
        self.client.publish(topic, json_data)

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
