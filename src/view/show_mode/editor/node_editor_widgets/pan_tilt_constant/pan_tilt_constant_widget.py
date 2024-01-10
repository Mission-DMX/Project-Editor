from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QScrollArea

from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import PanTiltConstantContentWidget


class PanTiltConstantWidget(NodeEditorFilterConfigWidget):

    def _get_configuration(self) -> dict[str, str]:
        return {'pan': '0.5', 'tilt': '30'}

    def _load_configuration(self, conf: dict[str, str]):
        pass

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        pass

    def _get_parameters(self) -> dict[str, str]:
        return {'pan': '0.8', 'tilt': '01'}

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self._parent_widget = QWidget(parent=parent)
        self._parent_widget.setMinimumHeight(300)
        self._parent_widget.setMaximumHeight(300)
        top_layout = QHBoxLayout()
        graph = PanTiltConstantContentWidget(self._parent_widget)
        top_layout.addWidget(graph)
        self._parent_widget.setLayout(top_layout)
