"""Dialog to add a new show UI widget."""

from collections.abc import Callable

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QDialog, QPushButton, QStackedLayout, QVBoxLayout, QWidget

from model import UIPage, UIWidget
from model.filter import FilterTypeEnumeration
from view.utility_widgets.button_container import ButtonContainer
from view.utility_widgets.filter_selection_widget import FilterSelectionWidget


class WidgetSetupDialog(QDialog):
    """Dialog to add a new show UI widget."""

    def __init__(
        self,
        parent: QWidget,
        allowed_filters: list[list[FilterTypeEnumeration]],
        callback: Callable,
        pos: QPoint,
        page: UIPage,
        swidget: UIWidget,
    ) -> None:
        """Initialize a new widget setup dialog.

        This dialog queries all required filters for setup and registers them with the new widget.

        Args:
            parent: The parent widget of this dialog.
            allowed_filters: The list of allowed filter types. For each entry, a filter conforming
                to the stated type is queried.
            callback: A callable receiving the widget and position, called once the dialog finishes.
            pos: The position where the widget should be placed.
            page: The UI page to place the widget into.
            swidget: The widget template to instantiate.

        """
        super().__init__(parent=parent, modal=True)
        self._instantiation_function = callback
        self._pos = pos
        self._page_index = 0
        self._swidget = swidget

        self._fsw = []
        horizontal_layout = QVBoxLayout()
        self._stack_layout = QStackedLayout()
        for filter_set in allowed_filters:
            widget = FilterSelectionWidget(self, page.scene, filter_set)
            widget.selected_filter_changed.connect(
                lambda new_filter_id: self._select_button.setEnabled(new_filter_id is not None)
            )
            self._fsw.append(widget)
            self._stack_layout.addWidget(widget)
        horizontal_layout.addLayout(self._stack_layout)
        self._select_button = QPushButton(self)
        self._select_button.setText("Select Filter")
        self._select_button.pressed.connect(self._select_pressed)
        self._select_button.setEnabled(False)
        self._bc = ButtonContainer(self)
        self._bc.add_button(self._select_button)
        horizontal_layout.addWidget(self._bc)
        self.setLayout(horizontal_layout)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.show()

    def _select_pressed(self) -> None:
        """Handle the filter selection and finishing of the dialog."""
        self._page_index += 1
        if self._page_index == len(self._fsw):
            for i in range(len(self._fsw)):
                self._swidget.set_filter(self._fsw[i].selected_filter, i)
            self._instantiation_function(self._swidget, self._pos)
            self.close()
        else:
            self._stack_layout.setCurrentIndex(self._page_index)
        self._select_button.setEnabled(True)
