from typing import TYPE_CHECKING

from model.control_desk import DeskColumn, ColorDeskColumn
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem
from view.utility_widgets.fader_column_selector import FaderColumnSelectorWidget

if TYPE_CHECKING:
    from model.virtual_filters.effects_stacks.effects.fader_input_effects import ColorInputEffect


class FaderSelectionConfigurationWidget(FaderColumnSelectorWidget):

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
