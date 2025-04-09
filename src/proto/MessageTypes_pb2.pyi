from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor
MSGT_ADD_FADER_BANK_SET: MsgType
MSGT_BUTTON_STATE_CHANGE: MsgType
MSGT_CURRENT_STATE_UPDATE: MsgType
MSGT_DELETE_UNIVERSE: MsgType
MSGT_DESK_UPDATE: MsgType
MSGT_DMX_OUTPUT: MsgType
MSGT_ENTER_SCENE: MsgType
MSGT_EVENT: MsgType
MSGT_EVENT_SENDER_UPDATE: MsgType
MSGT_FADER_POSITION: MsgType
MSGT_LOAD_SHOW_FILE: MsgType
MSGT_LOG_MESSAGE: MsgType
MSGT_NOTHING: MsgType
MSGT_REMOVE_FADER_BANK_SET: MsgType
MSGT_REQUEST_DMX_DATA: MsgType
MSGT_REQUEST_UNIVERSE_LIST: MsgType
MSGT_ROTARY_ENCODER_CHANGE: MsgType
MSGT_STATE_LIST: MsgType
MSGT_UNIVERSE: MsgType
MSGT_UNIVERSE_LIST: MsgType
MSGT_UPDATE_COLUMN: MsgType
MSGT_UPDATE_PARAMETER: MsgType
MSGT_UPDATE_STATE: MsgType

class MsgType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
