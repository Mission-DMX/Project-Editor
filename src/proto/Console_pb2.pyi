from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ButtonState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BS_SET_LED_NOT_ACTIVE: _ClassVar[ButtonState]
    BS_ACTIVE: _ClassVar[ButtonState]
    BS_SET_LED_BLINKING: _ClassVar[ButtonState]
    BS_BUTTON_PRESSED: _ClassVar[ButtonState]
    BS_BUTTON_RELEASED: _ClassVar[ButtonState]

class ButtonCode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    BTN_CH1_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH2_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH3_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH4_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH5_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH6_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH7_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH8_ENCODER_ROTARYMODE: _ClassVar[ButtonCode]
    BTN_CH1_REC_READY: _ClassVar[ButtonCode]
    BTN_CH2_REC_READY: _ClassVar[ButtonCode]
    BTN_CH3_REC_READY: _ClassVar[ButtonCode]
    BTN_CH4_REC_READY: _ClassVar[ButtonCode]
    BTN_CH5_REC_READY: _ClassVar[ButtonCode]
    BTN_CH6_REC_READY: _ClassVar[ButtonCode]
    BTN_CH7_REC_READY: _ClassVar[ButtonCode]
    BTN_CH8_REC_READY: _ClassVar[ButtonCode]
    BTN_CH1_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH2_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH3_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH4_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH5_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH6_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH7_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH8_SOLO_FLASH: _ClassVar[ButtonCode]
    BTN_CH1_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH2_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH3_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH4_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH5_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH6_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH7_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH8_MUTE_BLACK: _ClassVar[ButtonCode]
    BTN_CH1_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH2_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH3_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH4_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH5_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH6_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH7_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_CH8_SELECT_SELECT: _ClassVar[ButtonCode]
    BTN_TRACK_CONSOLE: _ClassVar[ButtonCode]
    BTN_PAN_EDITSHOW: _ClassVar[ButtonCode]
    BTN_EQ_SHOWUI: _ClassVar[ButtonCode]
    BTN_SEND_VISUALIZER: _ClassVar[ButtonCode]
    BTN_PLUGIN_PATCH: _ClassVar[ButtonCode]
    BTN_INST_DEBUG: _ClassVar[ButtonCode]
    BTN_NAMEVALUE_COMMITSHOW: _ClassVar[ButtonCode]
    BTN_BEATS_OOPS: _ClassVar[ButtonCode]
    BTN_GLOBALVIEW_COMMITRDY: _ClassVar[ButtonCode]
    BTN_MIDITRACKS_FIND: _ClassVar[ButtonCode]
    BTN_INPUTS_EVENTS: _ClassVar[ButtonCode]
    BTN_AUDIOTRACKS: _ClassVar[ButtonCode]
    BTN_AUDIOINST: _ClassVar[ButtonCode]
    BTN_AUX: _ClassVar[ButtonCode]
    BTN_BUSSES: _ClassVar[ButtonCode]
    BTN_OUTPUTS: _ClassVar[ButtonCode]
    BTN_USER: _ClassVar[ButtonCode]
    BTN_FLIP_MAINDARK: _ClassVar[ButtonCode]
    BTN_F1_F1: _ClassVar[ButtonCode]
    BTN_F2_F2: _ClassVar[ButtonCode]
    BTN_F3_F3: _ClassVar[ButtonCode]
    BTN_F4_F4: _ClassVar[ButtonCode]
    BTN_F5_F5: _ClassVar[ButtonCode]
    BTN_F6_F6: _ClassVar[ButtonCode]
    BTN_F7_F7: _ClassVar[ButtonCode]
    BTN_F8_F8: _ClassVar[ButtonCode]
    BTN_SHIFT: _ClassVar[ButtonCode]
    BTN_OPTION: _ClassVar[ButtonCode]
    BTN_CONTROL: _ClassVar[ButtonCode]
    BTN_ALT: _ClassVar[ButtonCode]
    BTN_READOFF_GOTO: _ClassVar[ButtonCode]
    BTN_WRITE_MOVEWINDOW: _ClassVar[ButtonCode]
    BTN_TOUCH: _ClassVar[ButtonCode]
    BTN_LATCH: _ClassVar[ButtonCode]
    BTN_TRIM: _ClassVar[ButtonCode]
    BTN_GROUP: _ClassVar[ButtonCode]
    BTN_SAVE_SAVE: _ClassVar[ButtonCode]
    BTN_UNDO_UNDO: _ClassVar[ButtonCode]
    BTN_CANCEL_CANCEL: _ClassVar[ButtonCode]
    BTN_ENTER_ENTER: _ClassVar[ButtonCode]
    BTN_MARKER_GOBO: _ClassVar[ButtonCode]
    BTN_NUDGE_STROBO: _ClassVar[ButtonCode]
    BTN_CYCLE_SHUTTER: _ClassVar[ButtonCode]
    BTN_DROP_COLOR: _ClassVar[ButtonCode]
    BTN_REPLACE_TEMPERATURE: _ClassVar[ButtonCode]
    BTN_CLICK_IMAGE: _ClassVar[ButtonCode]
    BTN_SOLO_SPEED: _ClassVar[ButtonCode]
    BTN_REV_LASTCUE: _ClassVar[ButtonCode]
    BTN_FF_NEXTCUE: _ClassVar[ButtonCode]
    BTN_STOP_STOPCUE: _ClassVar[ButtonCode]
    BTN_PLAY_RUNCUE: _ClassVar[ButtonCode]
    BTN_REC_RECFRAME: _ClassVar[ButtonCode]
    BTN_FADERBANKPREV_FADERBANKPREV: _ClassVar[ButtonCode]
    BTN_FADERBANKNEXT_FADERBANKNEXT: _ClassVar[ButtonCode]
    BTN_CHPREV_UNIVERSEPREV: _ClassVar[ButtonCode]
    BTN_CHNEXT_UNIVERSENEXT: _ClassVar[ButtonCode]
    BTN_SCRUB_JOGWHEELMODESWITCH: _ClassVar[ButtonCode]
    BTN_CROSSENTER: _ClassVar[ButtonCode]
    BTN_UP_UP: _ClassVar[ButtonCode]
    BTN_DOWN_DOWN: _ClassVar[ButtonCode]
    BTN_RIGHT_RIGHT: _ClassVar[ButtonCode]
    BTN_LEFT_LEFT: _ClassVar[ButtonCode]
    FADERTOUCH_CH1: _ClassVar[ButtonCode]
    FADERTOUCH_CH2: _ClassVar[ButtonCode]
    FADERTOUCH_CH3: _ClassVar[ButtonCode]
    FADERTOUCH_CH4: _ClassVar[ButtonCode]
    FADERTOUCH_CH5: _ClassVar[ButtonCode]
    FADERTOUCH_CH6: _ClassVar[ButtonCode]
    FADERTOUCH_CH7: _ClassVar[ButtonCode]
    FADERTOUCH_CH8: _ClassVar[ButtonCode]
    FADERTOUCH_MAIN: _ClassVar[ButtonCode]

class lcd_color(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    black: _ClassVar[lcd_color]
    red: _ClassVar[lcd_color]
    green: _ClassVar[lcd_color]
    yellow: _ClassVar[lcd_color]
    blue: _ClassVar[lcd_color]
    magenta: _ClassVar[lcd_color]
    cyan: _ClassVar[lcd_color]
    white: _ClassVar[lcd_color]
BS_SET_LED_NOT_ACTIVE: ButtonState
BS_ACTIVE: ButtonState
BS_SET_LED_BLINKING: ButtonState
BS_BUTTON_PRESSED: ButtonState
BS_BUTTON_RELEASED: ButtonState
BTN_CH1_ENCODER_ROTARYMODE: ButtonCode
BTN_CH2_ENCODER_ROTARYMODE: ButtonCode
BTN_CH3_ENCODER_ROTARYMODE: ButtonCode
BTN_CH4_ENCODER_ROTARYMODE: ButtonCode
BTN_CH5_ENCODER_ROTARYMODE: ButtonCode
BTN_CH6_ENCODER_ROTARYMODE: ButtonCode
BTN_CH7_ENCODER_ROTARYMODE: ButtonCode
BTN_CH8_ENCODER_ROTARYMODE: ButtonCode
BTN_CH1_REC_READY: ButtonCode
BTN_CH2_REC_READY: ButtonCode
BTN_CH3_REC_READY: ButtonCode
BTN_CH4_REC_READY: ButtonCode
BTN_CH5_REC_READY: ButtonCode
BTN_CH6_REC_READY: ButtonCode
BTN_CH7_REC_READY: ButtonCode
BTN_CH8_REC_READY: ButtonCode
BTN_CH1_SOLO_FLASH: ButtonCode
BTN_CH2_SOLO_FLASH: ButtonCode
BTN_CH3_SOLO_FLASH: ButtonCode
BTN_CH4_SOLO_FLASH: ButtonCode
BTN_CH5_SOLO_FLASH: ButtonCode
BTN_CH6_SOLO_FLASH: ButtonCode
BTN_CH7_SOLO_FLASH: ButtonCode
BTN_CH8_SOLO_FLASH: ButtonCode
BTN_CH1_MUTE_BLACK: ButtonCode
BTN_CH2_MUTE_BLACK: ButtonCode
BTN_CH3_MUTE_BLACK: ButtonCode
BTN_CH4_MUTE_BLACK: ButtonCode
BTN_CH5_MUTE_BLACK: ButtonCode
BTN_CH6_MUTE_BLACK: ButtonCode
BTN_CH7_MUTE_BLACK: ButtonCode
BTN_CH8_MUTE_BLACK: ButtonCode
BTN_CH1_SELECT_SELECT: ButtonCode
BTN_CH2_SELECT_SELECT: ButtonCode
BTN_CH3_SELECT_SELECT: ButtonCode
BTN_CH4_SELECT_SELECT: ButtonCode
BTN_CH5_SELECT_SELECT: ButtonCode
BTN_CH6_SELECT_SELECT: ButtonCode
BTN_CH7_SELECT_SELECT: ButtonCode
BTN_CH8_SELECT_SELECT: ButtonCode
BTN_TRACK_CONSOLE: ButtonCode
BTN_PAN_EDITSHOW: ButtonCode
BTN_EQ_SHOWUI: ButtonCode
BTN_SEND_VISUALIZER: ButtonCode
BTN_PLUGIN_PATCH: ButtonCode
BTN_INST_DEBUG: ButtonCode
BTN_NAMEVALUE_COMMITSHOW: ButtonCode
BTN_BEATS_OOPS: ButtonCode
BTN_GLOBALVIEW_COMMITRDY: ButtonCode
BTN_MIDITRACKS_FIND: ButtonCode
BTN_INPUTS_EVENTS: ButtonCode
BTN_AUDIOTRACKS: ButtonCode
BTN_AUDIOINST: ButtonCode
BTN_AUX: ButtonCode
BTN_BUSSES: ButtonCode
BTN_OUTPUTS: ButtonCode
BTN_USER: ButtonCode
BTN_FLIP_MAINDARK: ButtonCode
BTN_F1_F1: ButtonCode
BTN_F2_F2: ButtonCode
BTN_F3_F3: ButtonCode
BTN_F4_F4: ButtonCode
BTN_F5_F5: ButtonCode
BTN_F6_F6: ButtonCode
BTN_F7_F7: ButtonCode
BTN_F8_F8: ButtonCode
BTN_SHIFT: ButtonCode
BTN_OPTION: ButtonCode
BTN_CONTROL: ButtonCode
BTN_ALT: ButtonCode
BTN_READOFF_GOTO: ButtonCode
BTN_WRITE_MOVEWINDOW: ButtonCode
BTN_TOUCH: ButtonCode
BTN_LATCH: ButtonCode
BTN_TRIM: ButtonCode
BTN_GROUP: ButtonCode
BTN_SAVE_SAVE: ButtonCode
BTN_UNDO_UNDO: ButtonCode
BTN_CANCEL_CANCEL: ButtonCode
BTN_ENTER_ENTER: ButtonCode
BTN_MARKER_GOBO: ButtonCode
BTN_NUDGE_STROBO: ButtonCode
BTN_CYCLE_SHUTTER: ButtonCode
BTN_DROP_COLOR: ButtonCode
BTN_REPLACE_TEMPERATURE: ButtonCode
BTN_CLICK_IMAGE: ButtonCode
BTN_SOLO_SPEED: ButtonCode
BTN_REV_LASTCUE: ButtonCode
BTN_FF_NEXTCUE: ButtonCode
BTN_STOP_STOPCUE: ButtonCode
BTN_PLAY_RUNCUE: ButtonCode
BTN_REC_RECFRAME: ButtonCode
BTN_FADERBANKPREV_FADERBANKPREV: ButtonCode
BTN_FADERBANKNEXT_FADERBANKNEXT: ButtonCode
BTN_CHPREV_UNIVERSEPREV: ButtonCode
BTN_CHNEXT_UNIVERSENEXT: ButtonCode
BTN_SCRUB_JOGWHEELMODESWITCH: ButtonCode
BTN_CROSSENTER: ButtonCode
BTN_UP_UP: ButtonCode
BTN_DOWN_DOWN: ButtonCode
BTN_RIGHT_RIGHT: ButtonCode
BTN_LEFT_LEFT: ButtonCode
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
red: lcd_color
green: lcd_color
yellow: lcd_color
blue: lcd_color
magenta: lcd_color
cyan: lcd_color
white: lcd_color

class button_state_change(_message.Message):
    __slots__ = ("button", "new_state")
    BUTTON_FIELD_NUMBER: _ClassVar[int]
    NEW_STATE_FIELD_NUMBER: _ClassVar[int]
    button: ButtonCode
    new_state: ButtonState
    def __init__(self, button: _Optional[_Union[ButtonCode, str]] = ..., new_state: _Optional[_Union[ButtonState, str]] = ...) -> None: ...

class fader_position(_message.Message):
    __slots__ = ("column_id", "position")
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    column_id: str
    position: int
    def __init__(self, column_id: _Optional[str] = ..., position: _Optional[int] = ...) -> None: ...

class rotary_encoder_change(_message.Message):
    __slots__ = ("column_id", "amount")
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    column_id: str
    amount: int
    def __init__(self, column_id: _Optional[str] = ..., amount: _Optional[int] = ...) -> None: ...

class remove_fader_bank_set(_message.Message):
    __slots__ = ("bank_id",)
    BANK_ID_FIELD_NUMBER: _ClassVar[int]
    bank_id: str
    def __init__(self, bank_id: _Optional[str] = ...) -> None: ...

class desk_update(_message.Message):
    __slots__ = ("selected_column_id", "find_active_on_column_id", "jogwheel_change_since_last_update", "selected_bank_set", "selected_bank", "seven_seg_display_data")
    SELECTED_COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    FIND_ACTIVE_ON_COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    JOGWHEEL_CHANGE_SINCE_LAST_UPDATE_FIELD_NUMBER: _ClassVar[int]
    SELECTED_BANK_SET_FIELD_NUMBER: _ClassVar[int]
    SELECTED_BANK_FIELD_NUMBER: _ClassVar[int]
    SEVEN_SEG_DISPLAY_DATA_FIELD_NUMBER: _ClassVar[int]
    selected_column_id: str
    find_active_on_column_id: str
    jogwheel_change_since_last_update: int
    selected_bank_set: str
    selected_bank: int
    seven_seg_display_data: str
    def __init__(self, selected_column_id: _Optional[str] = ..., find_active_on_column_id: _Optional[str] = ..., jogwheel_change_since_last_update: _Optional[int] = ..., selected_bank_set: _Optional[str] = ..., selected_bank: _Optional[int] = ..., seven_seg_display_data: _Optional[str] = ...) -> None: ...

class fader_column(_message.Message):
    __slots__ = ("column_id", "upper_display_text", "lower_display_text", "display_color", "plain_color", "color_with_uv", "raw_data", "top_lcd_row_inverted", "bottom_lcd_row_inverted")
    class hsi_color(_message.Message):
        __slots__ = ("hue", "saturation", "intensity")
        HUE_FIELD_NUMBER: _ClassVar[int]
        SATURATION_FIELD_NUMBER: _ClassVar[int]
        INTENSITY_FIELD_NUMBER: _ClassVar[int]
        hue: float
        saturation: float
        intensity: float
        def __init__(self, hue: _Optional[float] = ..., saturation: _Optional[float] = ..., intensity: _Optional[float] = ...) -> None: ...
    class hsi_u_color(_message.Message):
        __slots__ = ("base", "uv")
        BASE_FIELD_NUMBER: _ClassVar[int]
        UV_FIELD_NUMBER: _ClassVar[int]
        base: fader_column.hsi_color
        uv: int
        def __init__(self, base: _Optional[_Union[fader_column.hsi_color, _Mapping]] = ..., uv: _Optional[int] = ...) -> None: ...
    class raw_fader_data(_message.Message):
        __slots__ = ("fader", "rotary_position", "meter_leds", "select", "b1", "b2", "b3")
        FADER_FIELD_NUMBER: _ClassVar[int]
        ROTARY_POSITION_FIELD_NUMBER: _ClassVar[int]
        METER_LEDS_FIELD_NUMBER: _ClassVar[int]
        SELECT_FIELD_NUMBER: _ClassVar[int]
        B1_FIELD_NUMBER: _ClassVar[int]
        B2_FIELD_NUMBER: _ClassVar[int]
        B3_FIELD_NUMBER: _ClassVar[int]
        fader: int
        rotary_position: int
        meter_leds: int
        select: ButtonState
        b1: ButtonState
        b2: ButtonState
        b3: ButtonState
        def __init__(self, fader: _Optional[int] = ..., rotary_position: _Optional[int] = ..., meter_leds: _Optional[int] = ..., select: _Optional[_Union[ButtonState, str]] = ..., b1: _Optional[_Union[ButtonState, str]] = ..., b2: _Optional[_Union[ButtonState, str]] = ..., b3: _Optional[_Union[ButtonState, str]] = ...) -> None: ...
    COLUMN_ID_FIELD_NUMBER: _ClassVar[int]
    UPPER_DISPLAY_TEXT_FIELD_NUMBER: _ClassVar[int]
    LOWER_DISPLAY_TEXT_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_COLOR_FIELD_NUMBER: _ClassVar[int]
    PLAIN_COLOR_FIELD_NUMBER: _ClassVar[int]
    COLOR_WITH_UV_FIELD_NUMBER: _ClassVar[int]
    RAW_DATA_FIELD_NUMBER: _ClassVar[int]
    TOP_LCD_ROW_INVERTED_FIELD_NUMBER: _ClassVar[int]
    BOTTOM_LCD_ROW_INVERTED_FIELD_NUMBER: _ClassVar[int]
    column_id: str
    upper_display_text: str
    lower_display_text: str
    display_color: lcd_color
    plain_color: fader_column.hsi_color
    color_with_uv: fader_column.hsi_u_color
    raw_data: fader_column.raw_fader_data
    top_lcd_row_inverted: bool
    bottom_lcd_row_inverted: bool
    def __init__(self, column_id: _Optional[str] = ..., upper_display_text: _Optional[str] = ..., lower_display_text: _Optional[str] = ..., display_color: _Optional[_Union[lcd_color, str]] = ..., plain_color: _Optional[_Union[fader_column.hsi_color, _Mapping]] = ..., color_with_uv: _Optional[_Union[fader_column.hsi_u_color, _Mapping]] = ..., raw_data: _Optional[_Union[fader_column.raw_fader_data, _Mapping]] = ..., top_lcd_row_inverted: bool = ..., bottom_lcd_row_inverted: bool = ...) -> None: ...

class add_fader_bank_set(_message.Message):
    __slots__ = ("bank_id", "default_active_fader_bank", "banks")
    class fader_bank(_message.Message):
        __slots__ = ("cols",)
        COLS_FIELD_NUMBER: _ClassVar[int]
        cols: _containers.RepeatedCompositeFieldContainer[fader_column]
        def __init__(self, cols: _Optional[_Iterable[_Union[fader_column, _Mapping]]] = ...) -> None: ...
    BANK_ID_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_ACTIVE_FADER_BANK_FIELD_NUMBER: _ClassVar[int]
    BANKS_FIELD_NUMBER: _ClassVar[int]
    bank_id: str
    default_active_fader_bank: int
    banks: _containers.RepeatedCompositeFieldContainer[add_fader_bank_set.fader_bank]
    def __init__(self, bank_id: _Optional[str] = ..., default_active_fader_bank: _Optional[int] = ..., banks: _Optional[_Iterable[_Union[add_fader_bank_set.fader_bank, _Mapping]]] = ...) -> None: ...
