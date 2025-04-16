from PySide6.QtWidgets import QDialog, QWidget, QVBoxLayout, QComboBox, QStackedLayout, QDialogButtonBox

from model import BoardConfiguration, Scene
from model.filter import FilterTypeEnumeration
from model.macro import Macro
from view.utility_widgets.filter_selection_widget import FilterSelectionWidget


class _CommandInsertionDialog(QDialog):
    def __init__(self, parent: QWidget, macro: Macro, supported_filter_list: list[FilterTypeEnumeration],
                 show: BoardConfiguration, update_callable: callable):
        super().__init__(parent)

        self._macro = macro
        self._show = show
        self._scene: Scene | None = None
        self._filter_id: str | None = None
        self._update_callable: callable = update_callable

        self._scene_selection_cb = QComboBox(self)
        self._scene_selection_cb.setEditable(False)
        self._scene_selection_cb.addItems(
            [s.human_readable_name if len(s.human_readable_name) > 0 else str(s.scene_id) for s in self._show.scenes]
        )
        self._scene_selection_cb.setCurrentIndex(-1)
        self._scene_selection_cb.currentIndexChanged.connect(self._scene_selected)

        self._filter_selection = FilterSelectionWidget(self, None, supported_filter_list)
        self._filter_selection.setEnabled(False)
        self._filter_selection.selected_filter_changed.connect(self._filter_selected)

        self._button_box = QDialogButtonBox(
            (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        )
        self._button_box.rejected.connect(self.close)
        self._button_box.accepted.connect(self._apply)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self._scene_selection_cb)
        layout.addWidget(self._filter_selection)

        self.custom_layout: QStackedLayout = QStackedLayout()
        layout.addLayout(self.custom_layout)

        layout.addWidget(self._button_box)

        self.setLayout(layout)

    def _scene_selected(self):
        if self._scene_selection_cb.count() == 0:
            return
        scene_index = self._scene_selection_cb.currentIndex()
        if scene_index == -1:
            return
        self._scene = self._show.scenes[scene_index]
        self._filter_selection.set_scene(self._scene)
        self._filter_selection.setEnabled(True)

    def _filter_selected(self, filter_id: str | None) -> None:
        if filter_id is not None:
            self._filter_id = filter_id
            self.on_filter_selected()
            self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def _apply(self):
        self._macro.content += "\n" + self.get_command()
        self._update_callable()
        self.close()

    def get_command(self) -> str:
        raise NotImplementedError()

    def on_filter_selected(self):
        raise NotImplementedError()
