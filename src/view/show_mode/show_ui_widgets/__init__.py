# coding=utf-8
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Type

from model import Filter, UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.show_mode.show_ui_widgets.autotracker.UIWidget import AutoTrackerUIWidget
from view.show_mode.show_ui_widgets.button_list_with_submit_value import ButtonsWithValueSubmit
from view.show_mode.show_ui_widgets.color_selection_uiwidget import ColorSelectionUIWidget
from view.show_mode.show_ui_widgets.cue_control import CueControlUIWidget
from view.show_mode.show_ui_widgets.debug_viz_widgets import ColorDebugVizWidget, NumberDebugVizWidget
from view.show_mode.show_ui_widgets.pan_tilt_constant_show_ui import PanTiltConstantControlUIWidget
from view.show_mode.show_ui_widgets.show_label import ShowLabelUIWidget

"""
The widget library contains information about widgets, provided by their slug. The infomration that is stored consists
out of the human readable name, the type required to instantiate a requested widget, the supported filter types (that
should be selected for construction) and a number indicating how many filters should be selected.
"""
WIDGET_LIBRARY: dict[str, tuple[str, Type[UIWidget], list[list[FilterTypeEnumeration]]]] = {
    "autotracker": ("Auto Tracker", AutoTrackerUIWidget, [[FilterTypeEnumeration.VFILTER_POSITION_CONSTANT, FilterTypeEnumeration.VFILTER_AUTOTRACKER]]),
    "buttonarray": ("Button Array", ButtonsWithValueSubmit, [[FilterTypeEnumeration.FILTER_CONSTANT_8BIT, FilterTypeEnumeration.FILTER_CONSTANT_16_BIT, FilterTypeEnumeration.FILTER_CONSTANT_FLOAT]]),
    "colorpicker": ("Color Picker", ColorSelectionUIWidget, [[FilterTypeEnumeration.FILTER_CONSTANT_COLOR]]),
    "cuecontrol": ("Cue Control", CueControlUIWidget, [[FilterTypeEnumeration.FILTER_TYPE_CUES, FilterTypeEnumeration.VFILTER_CUES]]),
    "pantiltconstant": ("Pan/Tilt Control", PanTiltConstantControlUIWidget, [[FilterTypeEnumeration.VFILTER_POSITION_CONSTANT]]),
    "label": ("Text Label", ShowLabelUIWidget, []),
    # TODO add direct inputs
    # TODO add fader update widgets
    "debug_color": ("Color Visualizer", ColorDebugVizWidget, [[FilterTypeEnumeration.FILTER_REMOTE_DEBUG_PIXEL]]),
    "debug_number": ("Number Output", NumberDebugVizWidget, [[FilterTypeEnumeration.FILTER_REMOTE_DEBUG_FLOAT, FilterTypeEnumeration.FILTER_REMOTE_DEBUG_16BIT, FilterTypeEnumeration.FILTER_REMOTE_DEBUG_8BIT]])
}


def get_widget_key(w: UIWidget) -> str | None:
    for k, v in WIDGET_LIBRARY.items():
        if isinstance(w, v[1]):
            return k
    return None


def filter_to_ui_widget(filter_: Filter, parent_page: "UIPage",
                        configuration: dict[str, str] | None = None) -> UIWidget:
    selected_configuration = configuration if configuration else dict()
    match filter_.filter_type:
        case 0 | 1 | 2:
            # number constants
            # TODO add choice for direct input
            return ButtonsWithValueSubmit(parent_page, selected_configuration)
        case 3:
            # color constant
            return ColorSelectionUIWidget(parent_page, selected_configuration)
        # case 39 | 40 | 41 | 42 | 43:
        #    # Faders: Update Color
        #    return None
        case FilterTypeEnumeration.FILTER_TYPE_CUES | FilterTypeEnumeration.VFILTER_CUES:
            # Cue Editor: play, pause, cue select, etc.
            return CueControlUIWidget(parent_page, selected_configuration)
        case FilterTypeEnumeration.VFILTER_POSITION_CONSTANT:
            # Constant pan tilt
            return PanTiltConstantControlUIWidget(parent_page, selected_configuration)
        case _:
            return None
