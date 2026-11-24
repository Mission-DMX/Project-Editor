from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
INVALID: event_type
ONGOING_EVENT: event_type
RELEASE: event_type
SINGLE_TRIGGER: event_type
START: event_type

class event(_message.Message):
    __slots__ = ["arguments", "event_id", "sender_function", "sender_id", "type"]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    EVENT_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_FUNCTION_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    arguments: _containers.RepeatedScalarFieldContainer[int]
    event_id: int
    sender_function: int
    sender_id: int
    type: event_type
    def __init__(self, type: _Optional[_Union[event_type, str]] = ..., sender_id: _Optional[int] = ..., sender_function: _Optional[int] = ..., event_id: _Optional[int] = ..., arguments: _Optional[_Iterable[int]] = ...) -> None: ...

class event_sender(_message.Message):
    __slots__ = ["configuration", "gui_debug_enabled", "name", "sender_id", "type"]
    class ConfigurationEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONFIGURATION_FIELD_NUMBER: _ClassVar[int]
    GUI_DEBUG_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    configuration: _containers.ScalarMap[str, str]
    gui_debug_enabled: bool
    name: str
    sender_id: int
    type: str
    def __init__(self, sender_id: _Optional[int] = ..., type: _Optional[str] = ..., name: _Optional[str] = ..., gui_debug_enabled: bool = ..., configuration: _Optional[_Mapping[str, str]] = ...) -> None: ...

class event_type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
