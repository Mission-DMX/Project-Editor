"""Widget containing a nodeeditor for one scene."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QVBoxLayout, QWidget

from editor.editor_tab.filter_page.filter_graph.filter_graph_view import FilterGraphWidget


class FilterPageTabWidget(QWidget):
    """Widget representing a Filter Page as a tab."""

    def __init__(self, filter_graph: FilterGraphWidget, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._layout = QVBoxLayout()
        self._toolbar = QToolBar(self)
        self._add_filter_action = QAction("Add Filter")
        self._add_filter_action.setEnabled(False)  # TODO implement behaviour (for touch screen use)
        self._toolbar.addAction(self._add_filter_action)
        self._layout.addWidget(self._toolbar)
        self._node_editor_widget = filter_graph
        self._layout.addWidget(self._node_editor_widget.widget)
        self.setLayout(self._layout)

    @property
    def node_editor(self) -> FilterGraphWidget:
        return self._node_editor_widget
