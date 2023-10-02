from model import Filter, UIWidget, UIPage
from view.show_mode.editor.show_ui_widgets.color_selection_uiwidget import ColorSelectionUIWidget
from view.show_mode.editor.show_ui_widgets.constant_button_list import ConstantNumberButtonList
from view.show_mode.editor.show_ui_widgets.cue_control import CueControlUIWidget


def filter_to_ui_widget(filter_: Filter, parent_page: "UIPage", configuration: dict[str, str] | None = None) -> UIWidget:
    selected_configuration = configuration if configuration else dict()
    match filter_.filter_type:
        case 0 | 1 | 2:
            # number constants
            # TODO add choice for direct input
            return ConstantNumberButtonList(filter_.filter_id, parent_page, filter_, selected_configuration)
        case 3:
            # color constant
            return ColorSelectionUIWidget(filter_.filter_id, parent_page, filter_, selected_configuration)
        # case 39 | 40 | 41 | 42 | 43:
        #    # Faders: Update Color
        #    return None
        case 44:
            # Cue Editor: play, pause, cue select, etc.
            return CueControlUIWidget(filter_.filter_id, parent_page, filter_, selected_configuration)
        case _:
            return None
