import asyncio
import logging

import grpc
import control_pb2
import control_pb2_grpc

from datetime import datetime

async def run() -> None:
    now = datetime.now()
    epoch = now.timestamp()

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = control_pb2_grpc.ControlAPIStub(channel)
        response = await stub.GetPrediction(control_pb2.State(x=epoch))
    #print("")
    logging.info("Greeter client received: %d", response.y)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())