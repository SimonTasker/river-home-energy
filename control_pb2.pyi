from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Prediction(_message.Message):
    __slots__ = ["y"]
    Y_FIELD_NUMBER: _ClassVar[int]
    y: float
    def __init__(self, y: _Optional[float] = ...) -> None: ...

class State(_message.Message):
    __slots__ = ["x"]
    X_FIELD_NUMBER: _ClassVar[int]
    x: float
    def __init__(self, x: _Optional[float] = ...) -> None: ...
