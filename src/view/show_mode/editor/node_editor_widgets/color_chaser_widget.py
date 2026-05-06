"""Contains ColorChaserFilterConfigWidget, ChaserLayerConfigWidget and associated helper classes.

For the model, please have a look under model.filter_data.chaser_model


"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtWidgets import QWidget

from model.filter_data.chaser_model import ChaserModel
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.cue_editor.yes_no_dialog import YesNoDialog

if TYPE_CHECKING:
    from PySide6.QtWidgets import QDialog
    from model import Filter


class ColorChaserFilterConfigWidget(NodeEditorFilterConfigWidget):
    """Editor widget for color chaser."""

    def __init__(self, filter: Filter):
        super().__init__()

        self._widget: QWidget = QWidget()
        self._input_dialog: QDialog | None = None
        self._live_updates_enabled = False
        self._model: ChaserModel | None = None

    def _enable_live_updates(self):
        self._live_updates_enabled = True

    @override
    def _get_configuration(self) -> dict[str, str]:
        return {}  # TODO

    @override
    def _load_configuration(self, conf: dict[str, str]) -> None:
        self._model = ChaserModel(conf)

    @override
    def get_widget(self) -> QWidget:
        return self._widget

    @override
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        pass  # TODO

    @override
    def _get_parameters(self) -> dict[str, str]:
        return {}  # TODO

    @override
    def parent_opened(self) -> None:
        self._live_updates_enabled = False
        self._input_dialog = YesNoDialog(
            self.get_widget(), "Preview", "Would you like to switch to live preview?", self._enable_live_updates
        )