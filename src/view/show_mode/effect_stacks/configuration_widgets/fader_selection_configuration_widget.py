# coding=utf-8

"""This file provides the fader input effect configuration widget."""

from typing import TYPE_CHECKING

from model.control_desk import ColorDeskColumn, DeskColumn
from view.utility_widgets.fader_column_selector import FaderColumnSelectorWidget

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.effects.fader_input_effects import ColorInputEffect


class FaderSelectionConfigurationWidget(FaderColumnSelectorWidget):
    """This widget enables the user to select a fader as the desired input."""

    def __init__(self, effect: "ColorInputEffect"):
        scene = effect.get_scene()
        if scene is not None:
            bankset = scene.linked_bankset
        else:
            bankset = None
        super().__init__(column_filter=ColorDeskColumn, base_set=bankset)
        self._effect = effect
        super().selection_changed.connect(self._column_selected)

    def setVisible(self, visible):
        self.load_values_from_effect()
        return super().setVisible(visible)

    def load_values_from_effect(self):
        f = self._effect.fader
        if f is None:
            return
        if f.bank_set is None:
            return
        self.set_selected_item(f.bank_set.id, f.id)

    def _column_selected(self, column: DeskColumn):
        self._effect.fader = column
