from PySide6.QtWidgets import QGridLayout, QLabel, QSpinBox, QWidget

from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget


class AutotrackerSettingsWidget(NodeEditorFilterConfigWidget):

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self._widget = QWidget(parent=parent)
        layout = QGridLayout()
        self._widget.setLayout(layout)
        layout.addWidget(QLabel("Number of trackers"), 0, 0)
        tracker_count_widget = QSpinBox(parent=self._widget)
        tracker_count_widget.setEnabled(False)
        tracker_count_widget.setValue(1)
        layout.addWidget(tracker_count_widget, 0, 1)
        layout.addWidget(QLabel("Other settings need to be configured from the player widget for now."), 1, 0)

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
