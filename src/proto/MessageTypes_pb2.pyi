from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class MsgType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    MSGT_NOTHING: _ClassVar[MsgType]
    MSGT_UPDATE_STATE: _ClassVar[MsgType]
    MSGT_CURRENT_STATE_UPDATE: _ClassVar[MsgType]
    MSGT_UNIVERSE: _ClassVar[MsgType]
    MSGT_UNIVERSE_LIST: _ClassVar[MsgType]
    MSGT_REQUEST_UNIVERSE_LIST: _ClassVar[MsgType]
    MSGT_DELETE_UNIVERSE: _ClassVar[MsgType]
    MSGT_BUTTON_STATE_CHANGE: _ClassVar[MsgType]
    MSGT_FADER_POSITION: _ClassVar[MsgType]
    MSGT_ROTARY_ENCODER_CHANGE: _ClassVar[MsgType]
    MSGT_DMX_OUTPUT: _ClassVar[MsgType]
    MSGT_REQUEST_DMX_DATA: _ClassVar[MsgType]
    MSGT_ENTER_SCENE: _ClassVar[MsgType]
    MSGT_LOAD_SHOW_FILE: _ClassVar[MsgType]
    MSGT_UPDATE_PARAMETER: _ClassVar[MsgType]
    MSGT_LOG_MESSAGE: _ClassVar[MsgType]
    MSGT_REMOVE_FADER_BANK_SET: _ClassVar[MsgType]
    MSGT_ADD_FADER_BANK_SET: _ClassVar[MsgType]
    MSGT_DESK_UPDATE: _ClassVar[MsgType]
    MSGT_UPDATE_COLUMN: _ClassVar[MsgType]
MSGT_NOTHING: MsgType
MSGT_UPDATE_STATE: MsgType
MSGT_CURRENT_STATE_UPDATE: MsgType
MSGT_UNIVERSE: MsgType
MSGT_UNIVERSE_LIST: MsgType
MSGT_REQUEST_UNIVERSE_LIST: MsgType
MSGT_DELETE_UNIVERSE: MsgType
MSGT_BUTTON_STATE_CHANGE: MsgType
MSGT_FADER_POSITION: MsgType
MSGT_ROTARY_ENCODER_CHANGE: MsgType
MSGT_DMX_OUTPUT: MsgType
MSGT_REQUEST_DMX_DATA: MsgType
MSGT_ENTER_SCENE: MsgType
MSGT_LOAD_SHOW_FILE: MsgType
MSGT_UPDATE_PARAMETER: MsgType
MSGT_LOG_MESSAGE: MsgType
MSGT_REMOVE_FADER_BANK_SET: MsgType
MSGT_ADD_FADER_BANK_SET: MsgType
MSGT_DESK_UPDATE: MsgType
MSGT_UPDATE_COLUMN: MsgType
