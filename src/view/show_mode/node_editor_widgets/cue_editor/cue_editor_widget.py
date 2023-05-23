from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar, QScrollArea, QHBoxLayout, QTableWidget, QTableWidgetItem, \
    QFormLayout, QComboBox

from view.show_mode.node_editor_widgets.cue_editor.cue import Cue, EndAction
from view.show_mode.node_editor_widgets.cue_editor.timeline_editor import TimelineContainer
from view.show_mode.node_editor_widgets.node_editor_widget import NodeEditorFilterConfigWidget


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
        cue_list_and_current_settings_container = QWidget()
        cue_list_and_current_settings_container_layout = QHBoxLayout()
        self._cue_list_widget = QTableWidget()
        self._cue_list_widget.setColumnCount(3)
        self._cue_list_widget.setHorizontalHeaderLabels(["Cue Number", "Duration", "End Action"])
        cue_list_and_current_settings_container_layout.addWidget(self._cue_list_widget)
        cue_settings_container = QWidget()
        cue_settings_container_layout = QFormLayout()
        self._current_cue_end_action_select_widget = QComboBox()
        self._current_cue_end_action_select_widget.insertItems(0, EndAction.formatted_value_list)
        cue_settings_container_layout.addRow("End Action", self._current_cue_end_action_select_widget)
        cue_settings_container.setLayout(cue_settings_container_layout)
        cue_list_and_current_settings_container_layout.addWidget(cue_settings_container)
        top_layout.addWidget(cue_list_and_current_settings_container)
        toolbar = QToolBar(parent=self._parent_widget)
        top_layout.addWidget(toolbar)
        v_scroll_area = QScrollArea()
        v_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        v_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # TODO link up/down button events to scrolling of v_scroll_area
        self._timeline_container = TimelineContainer()
        v_scroll_area.setWidget(self._timeline_container)
        top_layout.addWidget(v_scroll_area)
        self._parent_widget.setLayout(top_layout)
        self.add_cue(Cue())  # FIXME

    def add_cue(self, cue: Cue):
        target_row = self._cue_list_widget.rowCount() + 1
        self._cue_list_widget.setRowCount(target_row)
        self._cue_list_widget.setItem(target_row, 0, QTableWidgetItem(str(target_row)))
        self._cue_list_widget.setItem(target_row, 1, QTableWidgetItem(cue.duration_formatted))
        self._cue_list_widget.setItem(target_row, 2, QTableWidgetItem(str(cue)))
