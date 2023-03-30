"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import sys
import typing

if sys.version_info >= (3, 10):
    import typing as typing_extensions
else:
    import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _ButtonState:
    ValueType = typing.NewType("ValueType", builtins.int)
    V: typing_extensions.TypeAlias = ValueType

class _ButtonStateEnumTypeWrapper(google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[_ButtonState.ValueType], builtins.type):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    BS_SET_LED_NOT_ACTIVE: _ButtonState.ValueType  # 0
    BS_ACTIVE: _ButtonState.ValueType  # 1
    BS_SET_LED_BLINKING: _ButtonState.ValueType  # 2
    BS_BUTTON_PRESSED: _ButtonState.ValueType  # 3
    BS_BUTTON_RELEASED: _ButtonState.ValueType  # 4

class ButtonState(_ButtonState, metaclass=_ButtonStateEnumTypeWrapper):
    """
    This file specifies messages and types used for controlling the physical user interface
    """

BS_SET_LED_NOT_ACTIVE: ButtonState.ValueType  # 0
BS_ACTIVE: ButtonState.ValueType  # 1
BS_SET_LED_BLINKING: ButtonState.ValueType  # 2
BS_BUTTON_PRESSED: ButtonState.ValueType  # 3
BS_BUTTON_RELEASED: ButtonState.ValueType  # 4
global___ButtonState = ButtonState

@typing_extensions.final
class button_state_change(google.protobuf.message.Message):
    """This message can be send both ways:
    Fish -> UI: if a button was pressed
    UI -> Fish: Change the LED of a button
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    BUTTON_FIELD_NUMBER: builtins.int
    NEW_STATE_FIELD_NUMBER: builtins.int
    button: builtins.int
    new_state: global___ButtonState.ValueType
    def __init__(
        self,
        *,
        button: builtins.int = ...,
        new_state: global___ButtonState.ValueType = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["button", b"button", "new_state", b"new_state"]) -> None: ...

global___button_state_change = button_state_change

@typing_extensions.final
class fader_position(google.protobuf.message.Message):
    """This message can be used to set the fader position or be notified about a change done by the user"""

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    FADER_ID_FIELD_NUMBER: builtins.int
    POSITION_FIELD_NUMBER: builtins.int
    fader_id: builtins.int
    position: builtins.int
    def __init__(
        self,
        *,
        fader_id: builtins.int = ...,
        position: builtins.int = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["fader_id", b"fader_id", "position", b"position"]) -> None: ...

global___fader_position = fader_position

@typing_extensions.final
class rotary_encoder_change(google.protobuf.message.Message):
    """This message informs the UI about a rotary encoder change
    A positive value encodes n steps clock wise
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor

    ENCODER_ID_FIELD_NUMBER: builtins.int
    AMOUNT_FIELD_NUMBER: builtins.int
    encoder_id: builtins.int
    amount: builtins.int
    def __init__(
        self,
        *,
        encoder_id: builtins.int = ...,
        amount: builtins.int = ...,
    ) -> None: ...
    def ClearField(self, field_name: typing_extensions.Literal["amount", b"amount", "encoder_id", b"encoder_id"]) -> None: ...

global___rotary_encoder_change = rotary_encoder_change
