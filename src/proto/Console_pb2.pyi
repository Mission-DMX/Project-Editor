from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

BS_ACTIVE: ButtonState
BS_BUTTON_PRESSED: ButtonState
BS_BUTTON_RELEASED: ButtonState
BS_SET_LED_BLINKING: ButtonState
BS_SET_LED_NOT_ACTIVE: ButtonState
DESCRIPTOR: _descriptor.FileDescriptor

class button_state_change(_message.Message):
    __slots__ = ["button", "new_state"]
    BUTTON_FIELD_NUMBER: _ClassVar[int]
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    button: int
    new_state: ButtonState
    def __init__(self, button: _Optional[int] = ..., new_state: _Optional[_Union[ButtonState, str]] = ...) -> None: ...

class fader_position(_message.Message):
    __slots__ = ["fader_id", "position"]
    FADER_ID_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    fader_id: int
    position: int
    def __init__(self, fader_id: _Optional[int] = ..., position: _Optional[int] = ...) -> None: ...

class rotary_encoder_change(_message.Message):
    __slots__ = ["amount", "encoder_id"]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    ENCODER_ID_FIELD_NUMBER: _ClassVar[int]
    amount: int
    encoder_id: int
    def __init__(self, encoder_id: _Optional[int] = ..., amount: _Optional[int] = ...) -> None: ...

class ButtonState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
