from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ShowFileApplyState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SFAS_INVALID: _ClassVar[ShowFileApplyState]
    SFAS_SHOW_ACTIVE: _ClassVar[ShowFileApplyState]
    SFAS_SHOW_LOADING: _ClassVar[ShowFileApplyState]
    SFAS_SHOW_UPDATING: _ClassVar[ShowFileApplyState]
    SFAS_NO_SHOW_ERROR: _ClassVar[ShowFileApplyState]
    SFAS_ERROR_SHOW_RUNNING: _ClassVar[ShowFileApplyState]
SFAS_INVALID: ShowFileApplyState
SFAS_SHOW_ACTIVE: ShowFileApplyState
SFAS_SHOW_LOADING: ShowFileApplyState
SFAS_SHOW_UPDATING: ShowFileApplyState
SFAS_NO_SHOW_ERROR: ShowFileApplyState
SFAS_ERROR_SHOW_RUNNING: ShowFileApplyState

class enter_scene(_message.Message):
    __slots__ = ("scene_id",)
    SCENE_ID_FIELD_NUMBER: _ClassVar[int]
    scene_id: int
    def __init__(self, scene_id: _Optional[int] = ...) -> None: ...

class load_show_file(_message.Message):
    __slots__ = ("show_data", "goto_default_scene")
    SHOW_DATA_FIELD_NUMBER: _ClassVar[int]
    GOTO_DEFAULT_SCENE_FIELD_NUMBER: _ClassVar[int]
    show_data: str
    goto_default_scene: bool
    def __init__(self, show_data: _Optional[str] = ..., goto_default_scene: bool = ...) -> None: ...

class update_parameter(_message.Message):
    __slots__ = ("filter_id", "parameter_key", "parameter_value", "scene_id")
    FILTER_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMETER_KEY_FIELD_NUMBER: _ClassVar[int]
    PARAMETER_VALUE_FIELD_NUMBER: _ClassVar[int]
    SCENE_ID_FIELD_NUMBER: _ClassVar[int]
    filter_id: str
    parameter_key: str
    parameter_value: str
    scene_id: int
    def __init__(self, filter_id: _Optional[str] = ..., parameter_key: _Optional[str] = ..., parameter_value: _Optional[str] = ..., scene_id: _Optional[int] = ...) -> None: ...
