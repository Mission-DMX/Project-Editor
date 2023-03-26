from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Universe(_message.Message):
    __slots__ = ["id", "physical_location", "remote_location"]
    class ArtNet(_message.Message):
        __slots__ = ["ip_address", "port", "universe_on_device"]
        IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
        PORT_FIELD_NUMBER: _ClassVar[int]
        UNIVERSE_ON_DEVICE_FIELD_NUMBER: _ClassVar[int]
        ip_address: str
        port: int
        universe_on_device: int
        def __init__(self, ip_address: _Optional[str] = ..., port: _Optional[int] = ..., universe_on_device: _Optional[int] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    PHYSICAL_LOCATION_FIELD_NUMBER: _ClassVar[int]
    REMOTE_LOCATION_FIELD_NUMBER: _ClassVar[int]
    id: int
    physical_location: int
    remote_location: Universe.ArtNet
    def __init__(self, id: _Optional[int] = ..., physical_location: _Optional[int] = ..., remote_location: _Optional[_Union[Universe.ArtNet, _Mapping]] = ...) -> None: ...

class delete_universe(_message.Message):
    __slots__ = ["id"]
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class request_universe_list(_message.Message):
    __slots__ = ["universe_id"]
    UNIVERSE_ID_FIELD_NUMBER: _ClassVar[int]
    universe_id: int
    def __init__(self, universe_id: _Optional[int] = ...) -> None: ...

class universes_list(_message.Message):
    __slots__ = ["list_of_universes"]
    LIST_OF_UNIVERSES_FIELD_NUMBER: _ClassVar[int]
    list_of_universes: _containers.RepeatedCompositeFieldContainer[Universe]
    def __init__(self, list_of_universes: _Optional[_Iterable[_Union[Universe, _Mapping]]] = ...) -> None: ...
