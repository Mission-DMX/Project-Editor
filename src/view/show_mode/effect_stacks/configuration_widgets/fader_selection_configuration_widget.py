"""This file provides the fader input effect configuration widget."""
from __future__ import annotations

from typing import TYPE_CHECKING

from model.control_desk import ColorDeskColumn, DeskColumn
from view.utility_widgets.fader_column_selector import FaderColumnSelectorWidget

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.effects.fader_input_effects import ColorInputEffect


class FaderSelectionConfigurationWidget(FaderColumnSelectorWidget):
    """This widget enables the user to select a fader as the desired input."""

    def __init__(self, effect: ColorInputEffect) -> None:
        scene = effect.get_scene()
        bankset = scene.linked_bankset if scene is not None else None
        super().__init__(column_filter=ColorDeskColumn, base_set=bankset)
        self._effect = effect
        super().selection_changed.connect(self._column_selected)

    def setVisible(self, visible: bool) -> None:
        self.load_values_from_effect()
        return super().setVisible(visible)

    def load_values_from_effect(self) -> None:
        f = self._effect.fader
        if f is None:
            return
        if f.bank_set is None:
            return
        self.set_selected_item(f.bank_set.id, f.id)

    def _column_selected(self, column: DeskColumn) -> None:
        self._effect.fader = column
