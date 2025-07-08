
"""This widget provides an adapter to view the effect stacking editor widget as a filter config widget."""

from PySide6.QtWidgets import QWidget

from model import Filter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.effect_stacks.effects_stack_editor import EffectsStackEditor


class EffectsStackFilterConfigWidget(NodeEditorFilterConfigWidget):

    """This filter config widget provides a effect stack editor. Otherwise, it is just some glue-code."""

    def __init__(self, f: Filter):
        self._widget = EffectsStackEditor(f, None)

    def _get_configuration(self) -> dict[str, str]:
        return {}

    def _load_configuration(self, conf: dict[str, str]) -> None:
        pass

    def get_widget(self) -> QWidget:
        return self._widget

    def _load_parameters(self, parameters: dict[str, str]) -> None:
        pass

    def _get_parameters(self) -> dict[str, str]:
        return {}
