from typing import Callable

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from model import BoardConfiguration, Scene
from model.filter import FilterTypeEnumeration
from model.macro import Macro
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import Cue
from view.utility_widgets.filter_selection_widget import FilterSelectionWidget


class _InsertCueSwitchDialog(QDialog):
    def __init__(self, parent: QWidget, macro: Macro, show: BoardConfiguration, update_callable: Callable):
        QDialog.__init__(self, parent)
        self._macro = macro
        self._show = show
        self._scene: Scene | None = None
        self._filter_id: str | None = None
        self._update_callable: Callable = update_callable

        self._scene_selection_cb = QComboBox(self)
        self._scene_selection_cb.setEditable(False)
        self._scene_selection_cb.addItems(
            [s.human_readable_name if len(s.human_readable_name) > 0 else str(s.scene_id) for s in self._show.scenes]
        )
        self._scene_selection_cb.setCurrentIndex(-1)
        self._scene_selection_cb.currentIndexChanged.connect(self._scene_selected)

        self._filter_selection = FilterSelectionWidget(self, None, [
            FilterTypeEnumeration.FILTER_TYPE_CUES, FilterTypeEnumeration.VFILTER_CUES])
        self._filter_selection.setEnabled(False)
        self._filter_selection.selected_filter_changed.connect(self._filter_selected)

        self._cue_selection_cb = QComboBox(self)
        self._cue_selection_cb.setEditable(False)
        self._cue_selection_cb.setEnabled(False)

        self._button_box = QDialogButtonBox(
            (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        )
        self._button_box.rejected.connect(self.close)
        self._button_box.accepted.connect(self._apply)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self._scene_selection_cb)
        layout.addWidget(self._filter_selection)
        layout.addWidget(self._cue_selection_cb)
        layout.addWidget(self._button_box)
        self.setLayout(layout)

    def _apply(self):
        self._macro.content += f"\nshowctl filtermsg {self._scene.scene_id} {self._filter_id} run_cue {self._cue_selection_cb.currentIndex()}"
        self._update_callable()
        self.close()

    def _scene_selected(self):
        if self._scene_selection_cb.count() == 0:
            return
        scene_index = self._scene_selection_cb.currentIndex()
        if scene_index == -1:
            return
        self._scene = self._show.scenes[scene_index]
        self._filter_selection.set_scene(self._scene)
        self._filter_selection.setEnabled(True)
        self._scene_selection_cb.setEnabled(True)

    def _filter_selected(self, filter_id: str | None) -> None:
        if filter_id is not None:
            self._filter_id = filter_id
            self._cue_selection_cb.setEnabled(True)
            self._cue_selection_cb.clear()
            cue_model: list[Cue] = [Cue(s) for s in self._filter_selection.selected_filter.filter_configurations["cuelist"].split("$")]
            self._cue_selection_cb.addItems([c.name for c in cue_model])
            self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
