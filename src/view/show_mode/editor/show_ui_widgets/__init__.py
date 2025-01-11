from model import Filter, UIWidget, UIPage
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.show_ui_widgets.color_selection_uiwidget import ColorSelectionUIWidget
from view.show_mode.editor.show_ui_widgets.button_list_with_submit_value import ButtonsWithValueSubmit
from view.show_mode.editor.show_ui_widgets.color_swift_uiwidget import ColorSwiftUIWidget
from view.show_mode.editor.show_ui_widgets.cue_control import CueControlUIWidget
from view.show_mode.editor.show_ui_widgets.pan_tilt_constant_show_ui import PanTiltConstantControlUIWidget


def filter_to_ui_widget(filter_: Filter, parent_page: "UIPage", configuration: dict[str, str] | None = None,
                        variante: str = "") -> UIWidget:
    selected_configuration = configuration if configuration else dict()
    match filter_.filter_type:
        case 0 | 1 | 2:
            # number constants
            # TODO add choice for direct input
            return ButtonsWithValueSubmit(filter_.filter_id, parent_page, filter_, selected_configuration)
        case FilterTypeEnumeration.FILTER_CONSTANT_COLOR:
            # color constant
            #return ColorSelectionUIWidget(filter_.filter_id, parent_page, filter_, selected_configuration)
            return ColorSwiftUIWidget(filter_.filter_id, parent_page, filter_, selected_configuration)
        # case 39 | 40 | 41 | 42 | 43:
        #    # TODO Faders: Update Color
        #    return None
        case FilterTypeEnumeration.FILTER_TYPE_CUES | FilterTypeEnumeration.VFILTER_CUES:
            # Cue Editor: play, pause, cue select, etc.
            return CueControlUIWidget(filter_.filter_id, parent_page, filter_, selected_configuration)
        case FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            # Constant pan tilt
            return PanTiltConstantControlUIWidget(filter_.filter_id, parent_page, filter_, selected_configuration)
        case _:
            return None
