from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QScrollArea, QHBoxLayout

from model import DataType
from view.show_mode.node_editor_widgets.node_editor_widget import NodeEditorFilterConfigWidget


class TimelineContentWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        # TODO implement


class TimelineChannelLabel(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        # TODO implement


class TimelineContainer(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent=parent)
        layout = QHBoxLayout()
        self._channel_labels_panel = QWidget()
        self._channel_labels_panel_layout = QVBoxLayout()
        self._channel_labels_panel.setLayout(self._channel_labels_panel_layout)
        layout.addWidget(self._channel_labels_panel)
        self._keyframes_panel = QWidget()
        self._keyframes_panel_layout = QVBoxLayout()
        self._keyframes_panel.setLayout(self._keyframes_panel_layout)
        timeline_scroll_area = QScrollArea()
        timeline_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        timeline_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        timeline_scroll_area.setWidget(self._keyframes_panel)
        # TODO link jogwheel events to scrolling of cursor (and thus timeline_scroll_area)
        layout.addWidget(timeline_scroll_area)
        self.setLayout(layout)

    def add_channel(self, channel_type: DataType):
        # TODO add TimelineChannelLabel to self._channel_labels_panel_layout
        # TODO add TimelineContentWidget to self._keyframes_panel
        pass


class CueEditor(NodeEditorFilterConfigWidget):

    def _get_configuration(self) -> dict[str, str]:
        # TODO implement
        return dict()

    def _load_configuration(self, conf: dict[str, str]):
        # TODO implement
        pass

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        # TODO implement
        pass

    def _get_parameters(self) -> dict[str, str]:
        # TODO implement
        return dict()

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self._parent_widget = QWidget(parent=parent)
        top_layout = QVBoxLayout()
        toolbar = QToolBar(parent=self._parent_widget)
        top_layout.addWidget(toolbar)
        v_scroll_area = QScrollArea()
        v_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        v_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # TODO link up/down button events to scrolling of v_scroll_area
        self.timeline_container = TimelineContainer()
        v_scroll_area.setWidget(self.timeline_container)
        top_layout.addWidget(v_scroll_area)
        self._parent_widget.setLayout(top_layout)
