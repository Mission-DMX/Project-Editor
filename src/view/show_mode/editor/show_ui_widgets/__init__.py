from model import Filter, UIWidget, UIPage
from view.show_mode.editor.show_ui_widgets.constant_button_list import ConstantNumberButtonList
from view.show_mode.editor.show_ui_widgets.cue_control import CueControlUIWidget


def filter_to_ui_widget(filter_: Filter, parent_page: "UIPage") -> UIWidget:
    match filter_.filter_type:
        case 0 | 1 | 3:
            # number constants
            return ConstantNumberButtonList(filter_.filter_id, parent_page, filter_, dict())
        case 3:
            # color constant
            return None
        #case 39 | 40 | 41 | 42 | 43:
        #    # Faders: Update Color
        #    return None
        case 44:
            # Cue Editor: play, pause, cue select, etc.
            return CueControlUIWidget(filter_.filter_id, parent_page, filter_, dict())
        case 50:
            # Lua Widget: query for all data types?
            return None
        case _:
            return None
