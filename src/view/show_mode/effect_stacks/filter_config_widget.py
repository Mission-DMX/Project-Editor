"""Widget provides an adapter to view the effect stacking editor widget as a filter config widget."""

from typing import override

from PySide6.QtWidgets import QWidget

from model import Filter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.effect_stacks.effects_stack_editor import EffectsStackEditor


class EffectsStackFilterConfigWidget(NodeEditorFilterConfigWidget):
    """Filter config widget provides a effect stack editor. Otherwise, it is just some glue-code."""

    def __init__(self, f: Filter) -> None:
        """Initialize config widget using mandatory filter instance."""
        self._widget = EffectsStackEditor(f, None)

    @override
    def parent_opened(self) -> None:
        super().parent_opened()

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {}

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        pass

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> None:
        pass

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}
