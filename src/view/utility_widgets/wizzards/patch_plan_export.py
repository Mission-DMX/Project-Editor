import os.path
from pathlib import Path

from PySide6.QtWidgets import QWidget, QWizard, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QSpinBox, QListWidget, \
    QFileDialog

from model import BoardConfiguration
from view.utility_widgets.wizzards._composable_wizard_page import ComposableWizardPage


class PatchPlanExportWizard(QWizard):
    def __init__(self, parent: QWidget, show_data: BoardConfiguration):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(600, 300)
        self.setWindowTitle("Patch Plan Export")
        self._first_page = ComposableWizardPage()
        self._first_page.setTitle("Meta")
        layout = QFormLayout()
        self._export_panel = QWidget()
        export_layout = QHBoxLayout()
        self._export_location_tb = QLineEdit()
        self._location_select_button = QPushButton("Browse")
        self._location_select_button.clicked.connect(self._select_export_location)
        export_layout.addWidget(self._export_location_tb)
        export_layout.addWidget(self._location_select_button)
        self._export_panel.setLayout(export_layout)
        layout.addRow("Export Location:", self._export_panel)
        self._number_phases_sb = QSpinBox()
        self._number_phases_sb.setMinimum(1)
        self._number_phases_sb.setMaximum(16384)
        self._number_phases_sb.setSingleStep(1)
        self._number_phases_sb.setValue(1)
        layout.addRow("Number of Phases:", self._number_phases_sb)
        self._first_page.setLayout(layout)

        self._fixture_selection_page = ComposableWizardPage(page_activation_function=self._load_fixture_list,
                                                            check_completeness_function=self._commit_changes)
        self._fixture_selection_page.setTitle("Fixture Selection")
        self._fixture_selection_page.setSubTitle("Please select the fixtures that you would like to export")
        layout = QHBoxLayout()
        self._fixture_list = QListWidget()
        layout.addWidget(self._fixture_list)
        self._fixture_selection_page.setLayout(layout)

        self.addPage(self._first_page)
        self.addPage(self._fixture_selection_page)

        self._file_selection_dialog = QFileDialog(self, "Select Export Location")
        self._file_selection_dialog.setNameFilter("CSV (*.csv)")
        self._file_selection_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self._file_selection_dialog.setDefaultSuffix(".csv")
        self._file_selection_dialog.setDirectory(Path(show_data.file_path).parent.resolve() if len(show_data.file_path) > 1 else os.path.expanduser("~"))
        self._file_selection_dialog.fileSelected.connect(lambda file_name: self._export_location_tb.setText(file_name))

    def _select_export_location(self):
        self._file_selection_dialog.show()

    def _load_fixture_list(self, page: ComposableWizardPage):
        pass  # TODO

    def _commit_changes(self, page: ComposableWizardPage):
        # TODO
        return True