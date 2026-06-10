"""Contains ColorGroupWidget."""
from __future__ import annotations

from typing import TYPE_CHECKING

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
        layout.addWidget(QLabel("Please enter the name template and number of iterations.\n"
                                "Math filters are supported."))
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
        item = self._group_view.selectedItems()[0]
        if not isinstance(item, AnnotatedTreeWidgetItem):
            self._delete_button.setEnabled(False)
            return
        self._delete_button.setEnabled(True)
        enabled = item.annotated_data[0]
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
        name = self._input_dialog.textValue()
        self._input_dialog.deleteLater()
        self._input_dialog = None
        if name in self._model.output_groups:
            self._input_dialog = QMessageBox()
            self._input_dialog.setWindowTitle("Group Already Exists")
            self._input_dialog.setText("Group names need to be unique.")
            self._input_dialog.setIcon(QMessageBox.Icon.Critical)
            self._input_dialog.show()
            return
        self._model.output_groups[name] = []
        group_item = AnnotatedTreeWidgetItem(self._group_view)
        group_item.setText(0, name)
        group_item.annotated_data = (True, name)
        self._group_view.addTopLevelItem(group_item)

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
        name = self._input_dialog.textValue()
        self._input_dialog.deleteLater()
        self._input_dialog = None
        self._add_sub_output(name)

    def _add_sub_output(self, name: str) -> None:
        group_item = self._group_view.selectedItems()[0]
        if not isinstance(group_item, AnnotatedTreeWidgetItem):
            return
        group_name = group_item.annotated_data[1]
        self._model.output_groups[group_name].append(name)
        output_item = AnnotatedTreeWidgetItem(group_item)
        output_item.setText(0, name)
        output_item.annotated_data = (False, name)
        group_item.addChild(output_item)
        group_item.setExpanded(True)

    def _add_sub_output_range(self) -> None:
        if self._input_dialog is not None:
            self._input_dialog.deleteLater()
        self._input_dialog = _IterationAndTemplateDialog(self)
        self._input_dialog.accepted.connect(self._add_sub_output_range_final)
        self._input_dialog.show()

    def _add_sub_output_range_final(self) -> None:
        for name in self._input_dialog.generated_names:
            self._add_sub_output(name)
        self._input_dialog.deleteLater()
        self._input_dialog = None

    def _delete_selected_group_or_output(self) -> None:
        selected_item = self._group_view.selectedItems()
        if len(selected_item) == 0:
            return
        selected_item = selected_item[0]
        if not isinstance(selected_item, AnnotatedTreeWidgetItem):
            return
        is_group, name = selected_item.annotated_data
        if is_group:
            del self._model.output_groups[name]
            self._group_view.takeTopLevelItem(self._group_view.indexOfTopLevelItem(selected_item))
        else:
            group_item = selected_item.parent()
            if not isinstance(group_item, AnnotatedTreeWidgetItem):
                return
            _, group_name = group_item.annotated_data
            self._model.output_groups[group_name].remove(name)
            group_item.takeChild(group_item.indexOfChild(selected_item))
