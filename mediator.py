from __future__ import annotations

import datetime

# ================================================
class Mediator:
    # ================================================
    # Class Constructor
    def __init__(self, river_model: MediatedComponent, mqtt_client: MediatedComponent) -> None:
        self.river_model = river_model
        self.river_model.mediator = self
        self.mqtt_client = mqtt_client
        self.mqtt_client.mediator = self

    # ================================================
    def notify_mqtt_message(self, payload):
        # Format: yyyy-mm-ddTHH:MM:SS
        x = datetime.datetime.strptime(payload["Time"], '%Y-%m-%dT%H:%M:%S')
        # Require y
        y = payload["ENERGY"]["Today"]

        # train model on payload data
        self.river_model.train(x, y)

    # ================================================
    def notify_model_prediction(self, x, name, y):
        # Publish prediction
        self.mqtt_client.publish_prediction(x, name, y)

# ================================================
class MediatedComponent:
    # ================================================
    def __init__(self, mediator: Mediator = None) -> None:
        self._mediator = mediator

    # ================================================
    @property
    def mediator(self) -> Mediator:
        return self._mediator

    # ================================================
    @mediator.setter
    def mediator(self, mediator: Mediator) -> None:
        self._mediator = mediator