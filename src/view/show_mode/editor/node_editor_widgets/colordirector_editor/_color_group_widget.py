"""Contains ColorGroupWidget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import TemplateError
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from controller.cli.connect_command import get_math_enabled_jinja_env
from model.virtual_filters.colordirector_vfilter import is_valid_channel_name
from view.show_mode.editor.show_browser.annotated_item import AnnotatedTreeWidgetItem

if TYPE_CHECKING:
    from model.virtual_filters.colordirector_vfilter import ColordirectorVFilter


class _IterationAndTemplateDialog(QDialog):
    """Dialog to query iteration count and templates."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize using given parent."""
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Specify Sub Outputs")
        self.setMinimumWidth(300)
        layout = QFormLayout()
        layout.addWidget(
            QLabel("Please enter the name template and number of iterations.\nMath filters are supported.")
        )
        self._name_tb = QLineEdit()
        self._name_tb.setText("{{ i }}")
        self._name_tb.setPlaceholderText("Use Jinja Tag {{ i }} to access iterator.")
        layout.addRow("Name Template:", self._name_tb)
        self._iterator_sb = QSpinBox()
        self._iterator_sb.setMinimum(1)
        self._iterator_sb.setMaximum(16384)
        self._iterator_sb.setValue(2)
        layout.addRow("Iterations:", self._iterator_sb)
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._button_box.rejected.connect(self.close)
        self._button_box.accepted.connect(self.accept)
        layout.addWidget(self._button_box)
        self.setLayout(layout)

    @property
    def generated_names(self) -> list[str]:
        """Get the names the user generated."""
        jinja_env = get_math_enabled_jinja_env()
        template = jinja_env.from_string(self._name_tb.text())
        return [template.render({"i": i}) for i in range(self._iterator_sb.value())]


class ColorGroupWidget(QWidget):
    """Widget to edit color groups in color director vfilter."""

    groups_changed = Signal()

    def __init__(self, model: ColordirectorVFilter, parent: QWidget | None = None) -> None:
        """Initialize using given model and optional parent."""
        super().__init__(parent)
        self._model: ColordirectorVFilter = model
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        self._add_group_button = QPushButton("Add Group")
        self._add_group_button.clicked.connect(self._add_group)
        button_layout.addWidget(self._add_group_button)
        self._add_sub_output_button = QPushButton("Add Sub Output")
        self._add_sub_output_button.clicked.connect(self._add_sub_output_clicked)
        self._add_sub_output_button.setEnabled(False)
        button_layout.addWidget(self._add_sub_output_button)
        self._add_sub_output_range_button = QPushButton("Add Sub Output Range")
        self._add_sub_output_range_button.clicked.connect(self._add_sub_output_range)
        self._add_sub_output_range_button.setEnabled(False)
        button_layout.addWidget(self._add_sub_output_range_button)
        button_layout.addStretch()
        self._delete_button = QPushButton("Delete")
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._delete_selected_group_or_output)
        button_layout.addWidget(self._delete_button)
        layout.addLayout(button_layout)
        self._group_view = QTreeWidget(self)
        self._group_view.itemSelectionChanged.connect(self._selected_group_changed)
        self._group_view.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._group_view)
        self.setLayout(layout)
        self._input_dialog: QInputDialog | QMessageBox | _IterationAndTemplateDialog | None = None
        self._refresh_tree_view()

    def _refresh_tree_view(self) -> None:
        self._group_view.clear()
        for group, outputs in self._model.output_groups.items():
            group_item = AnnotatedTreeWidgetItem(self._group_view)
            group_item.setText(0, group)
            group_item.annotated_data = (True, group)
            for output in outputs:
                output_item = AnnotatedTreeWidgetItem(group_item)
                output_item.setText(0, output)
                output_item.annotated_data = (False, output)
                group_item.addChild(output_item)
            group_item.setExpanded(True)
            self._group_view.addTopLevelItem(group_item)

    def _selected_group_changed(self) -> None:
        selected_items = self._group_view.selectedItems()
        if len(selected_items) == 0:
            self._delete_button.setEnabled(False)
            self._add_sub_output_button.setEnabled(False)
            self._add_sub_output_range_button.setEnabled(False)
            return
        item = selected_items[0]
        if not isinstance(item, AnnotatedTreeWidgetItem):
            self._delete_button.setEnabled(False)
            return
        self._delete_button.setEnabled(True)
        annotated_data = item.annotated_data
        if not isinstance(annotated_data, tuple):
            return
        enabled = annotated_data[0]
        self._add_sub_output_button.setEnabled(enabled)
        self._add_sub_output_range_button.setEnabled(enabled)

    def _add_group(self) -> None:
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        self._input_dialog = QInputDialog(self)
        self._input_dialog.setModal(True)
        self._input_dialog.setLabelText("Please input group name:")
        self._input_dialog.setInputMode(QInputDialog.InputMode.TextInput)
        self._input_dialog.accepted.connect(self._add_group_final)
        self._input_dialog.show()

    def _add_group_final(self) -> None:
        dialog = self._input_dialog
        if not isinstance(dialog, QInputDialog):
            return
        name = dialog.textValue()
        dialog.deleteLater()
        self._input_dialog = None
        if not is_valid_channel_name(name):
            self._show_name_error(
                "Invalid Group Name",
                "Group names must not be empty and may only contain letters, digits, single underscores and "
                "hyphens. Double underscores and trailing underscores are not allowed.",
            )
            return
        if name in self._model.output_groups:
            self._show_name_error("Group Already Exists", "Group names need to be unique.")
            return
        self._model.output_groups[name] = []
        group_item = AnnotatedTreeWidgetItem(self._group_view)
        group_item.setText(0, name)
        group_item.annotated_data = (True, name)
        self._group_view.addTopLevelItem(group_item)
        self.groups_changed.emit()

    def _show_name_error(self, title: str, message: str) -> None:
        """Show an error message box informing about a rejected name.

        Args:
            title: The window title of the message box.
            message: The message explaining why the name was rejected.

        """
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        self._input_dialog = QMessageBox(self)
        self._input_dialog.setWindowTitle(title)
        self._input_dialog.setText(message)
        self._input_dialog.setIcon(QMessageBox.Icon.Critical)
        self._input_dialog.show()

    def _add_sub_output_clicked(self) -> None:
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        self._input_dialog = QInputDialog(self)
        self._input_dialog.setModal(True)
        self._input_dialog.setLabelText("Please input sub output name:")
        self._input_dialog.setInputMode(QInputDialog.InputMode.TextInput)
        self._input_dialog.accepted.connect(self._add_sub_output_final)
        self._input_dialog.show()

    def _add_sub_output_final(self) -> None:
        dialog = self._input_dialog
        if not isinstance(dialog, QInputDialog):
            return
        name = dialog.textValue()
        dialog.deleteLater()
        self._input_dialog = None
        if not self._add_sub_output(name):
            self._show_name_error(
                "Invalid Sub Output Name",
                "Sub output names must not be empty, must be unique within their group and may only contain "
                "letters, digits, single underscores and hyphens. Double underscores and trailing underscores are "
                "not allowed.",
            )

    def _add_sub_output(self, name: str) -> bool:
        """Add a sub output with the provided name to the currently selected group.

        Args:
            name: The name of the sub output to add.

        Returns:
            True if the sub output was added. False if no group is selected or the name is invalid or already
            present within the group.

        """
        selected_items = self._group_view.selectedItems()
        if len(selected_items) == 0:
            return False
        group_item = selected_items[0]
        if not isinstance(group_item, AnnotatedTreeWidgetItem):
            return False
        annotated_data = group_item.annotated_data
        if not isinstance(annotated_data, tuple) or len(annotated_data) < 2:
            return False
        group_name = annotated_data[1]
        if not is_valid_channel_name(name) or name in self._model.output_groups[group_name]:
            return False
        self._model.output_groups[group_name].append(name)
        output_item = AnnotatedTreeWidgetItem(group_item)
        output_item.setText(0, name)
        output_item.annotated_data = (False, name)
        group_item.addChild(output_item)
        group_item.setExpanded(True)
        return True

    def _add_sub_output_range(self) -> None:
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        self._input_dialog = _IterationAndTemplateDialog(self)
        self._input_dialog.accepted.connect(self._add_sub_output_range_final)
        self._input_dialog.show()

    def _add_sub_output_range_final(self) -> None:
        dialog = self._input_dialog
        if not isinstance(dialog, _IterationAndTemplateDialog):
            return
        try:
            generated_names = dialog.generated_names
        except (TemplateError, ValueError) as e:
            dialog.deleteLater()
            self._input_dialog = None
            self._show_name_error("Invalid Name Template", f"The entered name template is invalid: {e}")
            return
        skipped_count = 0
        for name in generated_names:
            if not self._add_sub_output(name):
                skipped_count += 1
        dialog.deleteLater()
        self._input_dialog = None
        if skipped_count > 0:
            self._show_name_error(
                "Skipped Sub Outputs",
                f"{skipped_count} generated sub output(s) were skipped because their names are invalid or already "
                "present within the group.",
            )

    def _delete_selected_group_or_output(self) -> None:
        selected_items = self._group_view.selectedItems()
        if len(selected_items) == 0:
            return
        selected_item = selected_items[0]
        if not isinstance(selected_item, AnnotatedTreeWidgetItem):
            return
        annotated_data = selected_item.annotated_data
        if not isinstance(annotated_data, tuple):
            return
        is_group, name = annotated_data
        if is_group:
            self._model.remove_output_group(name)
            self._group_view.takeTopLevelItem(self._group_view.indexOfTopLevelItem(selected_item))
            self.groups_changed.emit()
        else:
            group_item = selected_item.parent()
            if not isinstance(group_item, AnnotatedTreeWidgetItem):
                return
            parent_data = group_item.annotated_data
            if not isinstance(parent_data, tuple) or len(parent_data) < 2:
                return
            _, group_name = parent_data
            self._model.output_groups[group_name].remove(name)
            group_item.takeChild(group_item.indexOfChild(selected_item))
