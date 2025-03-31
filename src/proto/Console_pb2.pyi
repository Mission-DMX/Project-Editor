from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

BS_ACTIVE: ButtonState
BS_BUTTON_PRESSED: ButtonState
BS_BUTTON_RELEASED: ButtonState
BS_SET_LED_BLINKING: ButtonState
BS_SET_LED_NOT_ACTIVE: ButtonState
BTN_ALT: ButtonCode
BTN_AUDIOINST: ButtonCode
BTN_AUDIOTRACKS: ButtonCode
BTN_AUX: ButtonCode
BTN_BEATS_OOPS: ButtonCode
BTN_BUSSES: ButtonCode
BTN_CANCEL_CANCEL: ButtonCode
BTN_CH1_ENCODER_ROTARYMODE: ButtonCode
BTN_CH1_MUTE_BLACK: ButtonCode
BTN_CH1_REC_READY: ButtonCode
BTN_CH1_SELECT_SELECT: ButtonCode
BTN_CH1_SOLO_FLASH: ButtonCode
BTN_CH2_ENCODER_ROTARYMODE: ButtonCode
BTN_CH2_MUTE_BLACK: ButtonCode
BTN_CH2_REC_READY: ButtonCode
BTN_CH2_SELECT_SELECT: ButtonCode
BTN_CH2_SOLO_FLASH: ButtonCode
BTN_CH3_ENCODER_ROTARYMODE: ButtonCode
BTN_CH3_MUTE_BLACK: ButtonCode
BTN_CH3_REC_READY: ButtonCode
BTN_CH3_SELECT_SELECT: ButtonCode
BTN_CH3_SOLO_FLASH: ButtonCode
BTN_CH4_ENCODER_ROTARYMODE: ButtonCode
BTN_CH4_MUTE_BLACK: ButtonCode
BTN_CH4_REC_READY: ButtonCode
BTN_CH4_SELECT_SELECT: ButtonCode
BTN_CH4_SOLO_FLASH: ButtonCode
BTN_CH5_ENCODER_ROTARYMODE: ButtonCode
BTN_CH5_MUTE_BLACK: ButtonCode
BTN_CH5_REC_READY: ButtonCode
BTN_CH5_SELECT_SELECT: ButtonCode
BTN_CH5_SOLO_FLASH: ButtonCode
BTN_CH6_ENCODER_ROTARYMODE: ButtonCode
BTN_CH6_MUTE_BLACK: ButtonCode
BTN_CH6_REC_READY: ButtonCode
BTN_CH6_SELECT_SELECT: ButtonCode
BTN_CH6_SOLO_FLASH: ButtonCode
BTN_CH7_ENCODER_ROTARYMODE: ButtonCode
BTN_CH7_MUTE_BLACK: ButtonCode
BTN_CH7_REC_READY: ButtonCode
BTN_CH7_SELECT_SELECT: ButtonCode
BTN_CH7_SOLO_FLASH: ButtonCode
BTN_CH8_ENCODER_ROTARYMODE: ButtonCode
BTN_CH8_MUTE_BLACK: ButtonCode
BTN_CH8_REC_READY: ButtonCode
BTN_CH8_SELECT_SELECT: ButtonCode
BTN_CH8_SOLO_FLASH: ButtonCode
BTN_CHNEXT_UNIVERSENEXT: ButtonCode
BTN_CHPREV_UNIVERSEPREV: ButtonCode
BTN_CLICK_IMAGE: ButtonCode
BTN_CONTROL: ButtonCode
BTN_CROSSENTER: ButtonCode
BTN_CYCLE_SHUTTER: ButtonCode
BTN_DOWN_DOWN: ButtonCode
BTN_DROP_COLOR: ButtonCode
BTN_ENTER_ENTER: ButtonCode
BTN_EQ_SHOWUI: ButtonCode
BTN_F1_F1: ButtonCode
BTN_F2_F2: ButtonCode
BTN_F3_F3: ButtonCode
BTN_F4_F4: ButtonCode
BTN_F5_F5: ButtonCode
BTN_F6_F6: ButtonCode
BTN_F7_F7: ButtonCode
BTN_F8_F8: ButtonCode
BTN_FADERBANKNEXT_FADERBANKNEXT: ButtonCode
BTN_FADERBANKPREV_FADERBANKPREV: ButtonCode
BTN_FF_NEXTCUE: ButtonCode
BTN_FLIP_MAINDARK: ButtonCode
BTN_GLOBALVIEW_COMMITRDY: ButtonCode
BTN_GROUP: ButtonCode
BTN_INPUTS_EVENTS: ButtonCode
BTN_INST_DEBUG: ButtonCode
BTN_LATCH: ButtonCode
BTN_LEFT_LEFT: ButtonCode
BTN_MARKER_GOBO: ButtonCode
BTN_MIDITRACKS_FIND: ButtonCode
BTN_NAMEVALUE_COMMITSHOW: ButtonCode
BTN_NUDGE_STROBO: ButtonCode
BTN_OPTION: ButtonCode
BTN_OUTPUTS: ButtonCode
BTN_PAN_EDITSHOW: ButtonCode
BTN_PLAY_RUNCUE: ButtonCode
BTN_PLUGIN_PATCH: ButtonCode
BTN_READOFF_GOTO: ButtonCode
BTN_REC_RECFRAME: ButtonCode
BTN_REPLACE_TEMPERATURE: ButtonCode
BTN_REV_LASTCUE: ButtonCode
BTN_RIGHT_RIGHT: ButtonCode
BTN_SAVE_SAVE: ButtonCode
BTN_SCRUB_JOGWHEELMODESWITCH: ButtonCode
BTN_SEND_VISUALIZER: ButtonCode
BTN_SHIFT: ButtonCode
BTN_SOLO_SPEED: ButtonCode
BTN_STOP_STOPCUE: ButtonCode
BTN_TOUCH: ButtonCode
BTN_TRACK_CONSOLE: ButtonCode
BTN_TRIM: ButtonCode
BTN_UNDO_UNDO: ButtonCode
BTN_UP_UP: ButtonCode
BTN_USER: ButtonCode
BTN_WRITE_MOVEWINDOW: ButtonCode
DESCRIPTOR: _descriptor.FileDescriptor
FADERTOUCH_CH1: ButtonCode
FADERTOUCH_CH2: ButtonCode
FADERTOUCH_CH3: ButtonCode
FADERTOUCH_CH4: ButtonCode
FADERTOUCH_CH5: ButtonCode
FADERTOUCH_CH6: ButtonCode
FADERTOUCH_CH7: ButtonCode
FADERTOUCH_CH8: ButtonCode
FADERTOUCH_MAIN: ButtonCode
black: lcd_color
blue: lcd_color
cyan: lcd_color
green: lcd_color
magenta: lcd_color
red: lcd_color
white: lcd_color
yellow: lcd_color

class add_fader_bank_set(_message.Message):
    __slots__ = ["bank_id", "banks", "default_active_fader_bank"]
    class fader_bank(_message.Message):
        __slots__ = ["cols"]
        COLS_FIELD_NUMBER: _ClassVar[int]
        cols: _containers.RepeatedCompositeFieldContainer[fader_column]
        def __init__(self, cols: _Optional[_Iterable[_Union[fader_column, _Mapping]]] = ...) -> None: ...
    BANKS_FIELD_NUMBER: _ClassVar[int]
    BANK_ID_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_ACTIVE_FADER_BANK_FIELD_NUMBER: _ClassVar[int]
    bank_id: str
    banks: _containers.RepeatedCompositeFieldContainer[add_fader_bank_set.fader_bank]
    default_active_fader_bank: int
    def __init__(self, bank_id: _Optional[str] = ..., default_active_fader_bank: _Optional[int] = ..., banks: _Optional[_Iterable[_Union[add_fader_bank_set.fader_bank, _Mapping]]] = ...) -> None: ...

class button_state_change(_message.Message):
    __slots__ = ["button", "new_state"]
    BUTTON_FIELD_NUMBER: _ClassVar[int]
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    button: ButtonCode
    new_state: ButtonState
    def __init__(self, button: _Optional[_Union[ButtonCode, str]] = ..., new_state: _Optional[_Union[ButtonState, str]] = ...) -> None: ...

class desk_update(_message.Message):
    __slots__ = ["find_active_on_column_id", "jogwheel_change_since_last_update", "selected_bank", "selected_bank_set", "selected_column_id", "seven_seg_display_data"]
    FIND_ACTIVE_ON_COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    JOGWHEEL_CHANGE_SINCE_LAST_UPDATE_FIELD_NUMBER: _ClassVar[int]
    SELECTED_BANK_FIELD_NUMBER: _ClassVar[int]
    SELECTED_BANK_SET_FIELD_NUMBER: _ClassVar[int]
    SELECTED_COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    SEVEN_SEG_DISPLAY_DATA_FIELD_NUMBER: _ClassVar[int]
    find_active_on_column_id: str
    jogwheel_change_since_last_update: int
    selected_bank: int
    selected_bank_set: str
    selected_column_id: str
    seven_seg_display_data: str
    def __init__(self, selected_column_id: _Optional[str] = ..., find_active_on_column_id: _Optional[str] = ..., jogwheel_change_since_last_update: _Optional[int] = ..., selected_bank_set: _Optional[str] = ..., selected_bank: _Optional[int] = ..., seven_seg_display_data: _Optional[str] = ...) -> None: ...

class fader_column(_message.Message):
    __slots__ = ["bottom_lcd_row_inverted", "color_with_uv", "column_id", "display_color", "lower_display_text", "plain_color", "raw_data", "top_lcd_row_inverted", "upper_display_text"]
    class hsi_color(_message.Message):
        __slots__ = ["hue", "intensity", "saturation"]
        HUE_FIELD_NUMBER: _ClassVar[int]
        INTENSITY_FIELD_NUMBER: _ClassVar[int]
        SATURATION_FIELD_NUMBER: _ClassVar[int]
        hue: float
        intensity: float
        saturation: float
        def __init__(self, hue: _Optional[float] = ..., saturation: _Optional[float] = ..., intensity: _Optional[float] = ...) -> None: ...
    class hsi_u_color(_message.Message):
        __slots__ = ["base", "uv"]
        BASE_FIELD_NUMBER: _ClassVar[int]
        UV_FIELD_NUMBER: _ClassVar[int]
        base: fader_column.hsi_color
        uv: int
        def __init__(self, base: _Optional[_Union[fader_column.hsi_color, _Mapping]] = ..., uv: _Optional[int] = ...) -> None: ...
    class raw_fader_data(_message.Message):
        __slots__ = ["b1", "b2", "b3", "fader", "meter_leds", "rotary_position", "select"]
        B1_FIELD_NUMBER: _ClassVar[int]
        B2_FIELD_NUMBER: _ClassVar[int]
        B3_FIELD_NUMBER: _ClassVar[int]
        FADER_FIELD_NUMBER: _ClassVar[int]
        METER_LEDS_FIELD_NUMBER: _ClassVar[int]
        ROTARY_POSITION_FIELD_NUMBER: _ClassVar[int]
        SELECT_FIELD_NUMBER: _ClassVar[int]
        b1: ButtonState
        b2: ButtonState
        b3: ButtonState
        fader: int
        meter_leds: int
        rotary_position: int
        select: ButtonState
        def __init__(self, fader: _Optional[int] = ..., rotary_position: _Optional[int] = ..., meter_leds: _Optional[int] = ..., select: _Optional[_Union[ButtonState, str]] = ..., b1: _Optional[_Union[ButtonState, str]] = ..., b2: _Optional[_Union[ButtonState, str]] = ..., b3: _Optional[_Union[ButtonState, str]] = ...) -> None: ...
    BOTTOM_LCD_ROW_INVERTED_FIELD_NUMBER: _ClassVar[int]
    COLOR_WITH_UV_FIELD_NUMBER: _ClassVar[int]
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_COLOR_FIELD_NUMBER: _ClassVar[int]
    LOWER_DISPLAY_TEXT_FIELD_NUMBER: _ClassVar[int]
    PLAIN_COLOR_FIELD_NUMBER: _ClassVar[int]
    RAW_DATA_FIELD_NUMBER: _ClassVar[int]
    TOP_LCD_ROW_INVERTED_FIELD_NUMBER: _ClassVar[int]
    UPPER_DISPLAY_TEXT_FIELD_NUMBER: _ClassVar[int]
    bottom_lcd_row_inverted: bool
    color_with_uv: fader_column.hsi_u_color
    column_id: str
    display_color: lcd_color
    lower_display_text: str
    plain_color: fader_column.hsi_color
    raw_data: fader_column.raw_fader_data
    top_lcd_row_inverted: bool
    upper_display_text: str
    def __init__(self, column_id: _Optional[str] = ..., upper_display_text: _Optional[str] = ..., lower_display_text: _Optional[str] = ..., display_color: _Optional[_Union[lcd_color, str]] = ..., plain_color: _Optional[_Union[fader_column.hsi_color, _Mapping]] = ..., color_with_uv: _Optional[_Union[fader_column.hsi_u_color, _Mapping]] = ..., raw_data: _Optional[_Union[fader_column.raw_fader_data, _Mapping]] = ..., top_lcd_row_inverted: bool = ..., bottom_lcd_row_inverted: bool = ...) -> None: ...

class fader_position(_message.Message):
    __slots__ = ["column_id", "position"]
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    column_id: str
    position: int
    def __init__(self, column_id: _Optional[str] = ..., position: _Optional[int] = ...) -> None: ...

class remove_fader_bank_set(_message.Message):
    __slots__ = ["bank_id"]
    BANK_ID_FIELD_NUMBER: _ClassVar[int]
    bank_id: str
    def __init__(self, bank_id: _Optional[str] = ...) -> None: ...

class rotary_encoder_change(_message.Message):
    __slots__ = ["amount", "column_id"]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    amount: int
    column_id: str
    def __init__(self, column_id: _Optional[str] = ..., amount: _Optional[int] = ...) -> None: ...

class ButtonState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class ButtonCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class lcd_color(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
