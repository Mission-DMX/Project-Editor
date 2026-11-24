from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class dmx_output(_message.Message):
    __slots__ = ["channel_data", "universe_id"]
    CHANNEL_DATA_FIELD_NUMBER: _ClassVar[int]
    UNIVERSE_ID_FIELD_NUMBER: _ClassVar[int]
    channel_data: _containers.RepeatedScalarFieldContainer[int]
    universe_id: int
    def __init__(self, universe_id: _Optional[int] = ..., channel_data: _Optional[_Iterable[int]] = ...) -> None: ...

class request_dmx_data(_message.Message):
    __slots__ = ["universe_id"]
    UNIVERSE_ID_FIELD_NUMBER: _ClassVar[int]
    universe_id: int
    def __init__(self, universe_id: _Optional[int] = ...) -> None: ...
