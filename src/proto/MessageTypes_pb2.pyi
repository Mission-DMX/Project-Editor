"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _MsgType:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _MsgTypeEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_MsgType.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    MSGT_NOTHING: _MsgType.ValueType  # 0
    MSGT_UPDATE_STATE: _MsgType.ValueType  # 1
    MSGT_CURRENT_STATE_UPDATE: _MsgType.ValueType  # 2
    MSGT_UNIVERSE: _MsgType.ValueType  # 3
    MSGT_UNIVERSE_LIST: _MsgType.ValueType  # 4
    MSGT_REQUEST_UNIVERSE_LIST: _MsgType.ValueType  # 5
    MSGT_DELETE_UNIVERSE: _MsgType.ValueType  # 6
    MSGT_BUTTON_STATE_CHANGE: _MsgType.ValueType  # 7
    MSGT_FADER_POSITION: _MsgType.ValueType  # 8
    MSGT_ROTARY_ENCODER_CHANGE: _MsgType.ValueType  # 9
    MSGT_DMX_OUTPUT: _MsgType.ValueType  # 10
    MSGT_REQUEST_DMX_DATA: _MsgType.ValueType  # 11
    MSGT_ENTER_SCENE: _MsgType.ValueType  # 12
    MSGT_LOAD_SHOW_FILE: _MsgType.ValueType  # 13
    MSGT_UPDATE_PARAMETER: _MsgType.ValueType  # 14
    MSGT_LOG_MESSAGE: _MsgType.ValueType  # 15
    MSGT_REMOVE_FADER_BANK_SET: _MsgType.ValueType  # 16
    MSGT_ADD_FADER_BANK_SET: _MsgType.ValueType  # 17

class MsgType(_MsgType, metaclass=_MsgTypeEnumTypeWrapper): ...

MSGT_NOTHING: MsgType.ValueType  # 0
MSGT_UPDATE_STATE: MsgType.ValueType  # 1
MSGT_CURRENT_STATE_UPDATE: MsgType.ValueType  # 2
MSGT_UNIVERSE: MsgType.ValueType  # 3
MSGT_UNIVERSE_LIST: MsgType.ValueType  # 4
MSGT_REQUEST_UNIVERSE_LIST: MsgType.ValueType  # 5
MSGT_DELETE_UNIVERSE: MsgType.ValueType  # 6
MSGT_BUTTON_STATE_CHANGE: MsgType.ValueType  # 7
MSGT_FADER_POSITION: MsgType.ValueType  # 8
MSGT_ROTARY_ENCODER_CHANGE: MsgType.ValueType  # 9
MSGT_DMX_OUTPUT: MsgType.ValueType  # 10
MSGT_REQUEST_DMX_DATA: MsgType.ValueType  # 11
MSGT_ENTER_SCENE: MsgType.ValueType  # 12
MSGT_LOAD_SHOW_FILE: MsgType.ValueType  # 13
MSGT_UPDATE_PARAMETER: MsgType.ValueType  # 14
MSGT_LOG_MESSAGE: MsgType.ValueType  # 15
MSGT_REMOVE_FADER_BANK_SET: MsgType.ValueType  # 16
MSGT_ADD_FADER_BANK_SET: MsgType.ValueType  # 17
global___MsgType = MsgType
