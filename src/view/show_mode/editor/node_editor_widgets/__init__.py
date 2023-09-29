# coding=utf-8
"""Node editor widgets"""

from model import Filter
from .lua_widget import LuaScriptConfigWidget
from .node_editor_widget import NodeEditorFilterConfigWidget
from .standard_widget import StandardWidget
from .cue_editor import CueEditor
from .column_select import ColumnSelect


def filter_to_ui_widget(filter_: Filter) -> NodeEditorFilterConfigWidget:
    match filter_.filter_type:
        case 39 | 40 | 41 | 42 | 43:
            return ColumnSelect()
        case 44:
            return CueEditor()
        case 50:
            return LuaScriptConfigWidget()
        case _:
            return StandardWidget(filter_)
