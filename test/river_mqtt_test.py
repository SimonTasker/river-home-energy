# MQTT Imports
import paho.mqtt.client as mqtt
from datetime import datetime
import json

# River imports
from river import linear_model
from river import preprocessing
from river import metrics
import pickle

# grpc imports
import grpc
from control_pb2 import State
from control_pb2 import Prediction
from control_pb2_grpc import ControlAPIServicer
from control_pb2_grpc import add_ControlAPIServicer_to_server

# Application imports
import configparser
import asyncio
import logging
import os

# ================================================

# Default data directory
data_dir = '/data'

# ================================================
# Logger Configuration and Setup

# Set logger configuration to dump everything to file
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=data_dir+'/river_energy.log',
                    filemode='w')

# Add stream handler that logs INFO messages
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# Format the stream handler the same as file, without time
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
# add handler to root logger
logging.getLogger('').addHandler(console)

# Define loggers
mqtt_logger = logging.getLogger('MQTT')
river_logger = logging.getLogger('River')
grpc_logger = logging.getLogger('gRPC')

# ================================================


# Default model parameters
scale = preprocessing.StandardScaler()
learn = linear_model.LinearRegression()
model = scale | learn

# Metrics
metric = metrics.MAE()

y_trues = []
y_preds = []

model_file = ''

# Coroutines to be invoked when the event loop is shutting down.
_cleanup_coroutines = []

# ================================================
# Update model with new data
def train(model, json_payload):

    river_logger.debug("Training model")

    # Format: yyyy-mm-ddTHH:MM:SS
    dt = datetime.strptime(json_payload["Time"], '%Y-%m-%dT%H:%M:%S')
    # Custom x values - derived from message payload
    x = { 'epoch' : dt.timestamp() }
    # Require y
    y = json_payload["ENERGY"]["Power"]

    # Make a prediction given current model
    y_pred = model.predict_one(x)
    # Learn from new data
    model.learn_one(x, y)

    # Update metrics based on prediction to actual
    metric.update(y, y_pred)

    y_trues.append(y)
    y_preds.append(y_pred)

    # Update saved model
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)

# ================================================
# Callback from MQTT connection attempt
def on_connect(client, userdata, flags, rc):
    # Only subscribe to topic if rc == 0
    if rc == 0:
        mqtt_logger.info("Connected and subscribing to topics")
        # Topic subscription packaged into userdata
        client.subscribe(userdata)
    else:
        mqtt_logger.critical("Failed to connect, rc: %s", rc)

# ================================================
# Callback from MQTT connection attempt
def on_message(client, userdata, message):
    # unpack message payload into json
    payload = message.payload.decode("utf-8")
    json_payload = json.loads(payload)

    mqtt_logger.debug("Received message: " + str(json_payload))

    # train model on payload data
    train(model, json_payload)

# ================================================
class API(ControlAPIServicer):
    async def GetPrediction(self,
                            request: State,
                            context: grpc.aio.ServicerContext) -> Prediction:
        grpc_logger.info("Serving GetPrediction request %d", request.x)
        x = { 'epoch' : request.x }
        return Prediction(y=model.predict_one(x))
    
# ================================================
async def serve() -> None:
    server = grpc.aio.server()
    add_ControlAPIServicer_to_server(API(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    grpc_logger.info("Starting server on %s", listen_addr)
    await server.start()

    async def server_graceful_shutdown():
        grpc_logger.info("Starting graceful shutdown...")
        # Shuts down the server with 5 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await server.stop(5)

    _cleanup_coroutines.append(server_graceful_shutdown())
    await server.wait_for_termination()

# ================================================
def read_config():
    config = configparser.ConfigParser()
    config.read(data_dir+'/configuration.ini')
    return config

# ================================================
# Main
if __name__ == "__main__":
    config = read_config()

    # On start up, check if model file already exists
    model_file = data_dir + "/" + config["River Settings"]["Model File"]

    if os.path.exists(model_file):
        river_logger.info("Found and loading existing model")
        with open(model_file, 'rb') as f:
            model = pickle.load(f)

    # Create the MQTT Client
    client = mqtt.Client()
    client.enable_logger(logger=mqtt_logger)
    # Register callbacks
    client.on_connect=on_connect
    client.on_message=on_message

    # Read mqtt config items
    mqtt_address = config["MQTT Settings"]["Address"]
    mqtt_port = int(config["MQTT Settings"]["Port"])
    mqtt_subscription = config["MQTT Settings"]["Topic"]

    # Set user data as the subscription address
    # This is so that it's passed through the on_connect callback
    client.user_data_set(mqtt_subscription)

    # Asynchronously connect client to MQTT stream
    client.connect_async(mqtt_address, mqtt_port, 60)

    # Start MQTT client async loop
    client.loop_start()

    loop = asyncio.get_event_loop()

    # Start gRPC interface
    try:
        loop.run_until_complete(serve())
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        mqtt_logger.debug("Stopping MQTT Loop")
        client.loop_stop()
        loop.close()