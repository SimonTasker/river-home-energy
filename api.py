# grpc imports
import grpc
from control_pb2 import State
from control_pb2 import Prediction
from control_pb2_grpc import ControlAPIServicer
from control_pb2_grpc import add_ControlAPIServicer_to_server

# Application imports
import logging

# ================================================
class API(ControlAPIServicer):
    # ================================================
    # Class Constructor
    def __init__(self, config, river_model):
        super().__init__()

        self.river_model = river_model

        # Define loggers
        self.grpc_logger = logging.getLogger('gRPC')

        self.server = grpc.io.server()
        self.listen_address = config['gRPC Settings']['Address']
        self.server.add_insecure_port(self.listen_address)

    # ================================================
    async def serve(self) -> None:
        add_ControlAPIServicer_to_server(self, self.server)
        self.grpc_logger.info("Starting server on %s", self.listen_address)
        await self.server.start()
        await self.server.wait_for_termination()

    # ================================================
    async def graceful_shutdown(self) -> None:
        self.grpc_logger.info("Starting graceful shutdown...")
        # Shuts down the server with 5 seconds of grace period. During the
        # grace period, the server won't accept new connections and allow
        # existing RPCs to continue within the grace period.
        await self.server.stop(5)

    # ================================================
    async def GetPrediction(self, request, context) -> Prediction:
        self.grpc_logger.info("Serving GetPrediction request %d", request.x)
        x = { 'epoch' : request.x }
        y = self.river_model.predict_one(x)
        return Prediction(y)