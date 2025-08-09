"""Wizard for automatically exporting the configured patch plan as a spreadsheet."""

import csv
import os.path
from collections import Counter
from logging import getLogger
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QWidget,
    QWizard,
)

from controller.utils.process_notifications import get_process_notifier
from model import BoardConfiguration
from model.ofl.fixture import UsedFixture
from view.show_mode.editor.show_browser.annotated_item import AnnotatedListWidgetItem
from view.utility_widgets.wizzards._composable_wizard_page import ComposableWizardPage

logger = getLogger(__name__)


class PatchPlanExportWizard(QWizard):
    """Wizard to export the patching configuration as a CSV file, including a power distribution guide."""

    def __init__(self, parent: QWidget, show_data: BoardConfiguration) -> None:
        """Wizard to export the patching configuration as a CSV file, including a power distribution guide."""
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumSize(600, 300)
        self.setWindowTitle("Patch Plan Export")
        self._first_page = ComposableWizardPage(
            check_completeness_function=lambda _: len(self._export_location_tb.text()) > 1
        )
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
        self._number_phases_sb.setValue(3)
        layout.addRow("Number of Phases:", self._number_phases_sb)
        # TODO add radio boxes to switch between bin packing (optimizing number of phases)
        #  vs load distribution on given phases (as currently implemented)
        # TODO allow weights to prioritize putting near fixtures on the same phase at the expense of uneven load
        self._first_page.setLayout(layout)

        self._fixture_selection_page = ComposableWizardPage(
            page_activation_function=self._load_fixture_list, check_completeness_function=self._commit_changes
        )
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
        self._file_selection_dialog.setDirectory(
            str(Path(show_data.file_path).parent.resolve()) if len(show_data.file_path) > 1 else os.path.expanduser("~")
        )
        self._file_selection_dialog.fileSelected.connect(self._export_location_selected)

        self._show = show_data

    def _select_export_location(self) -> None:
        """Prompt the user to select a CSV file export destination."""
        self._file_selection_dialog.show()

    def _export_location_selected(self, file_name: str) -> None:
        """Apply the path of the user-selected location to the text box."""
        self._export_location_tb.setText(file_name)
        self._first_page.completeChanged.emit()

    def _load_fixture_list(self, _: ComposableWizardPage) -> None:
        """Load all available fixtures into the list widget and prompt the user to select one for export."""
        for fixture in self._show.fixtures:
            item = AnnotatedListWidgetItem(self._fixture_list)
            item.setText(str(fixture))
            item.annotated_data = fixture
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)

    def _commit_changes(self, _: ComposableWizardPage) -> bool:
        """Generate the export after the user finishes the wizard."""
        pn = get_process_notifier("Export Fixtures to CSV list", 3)
        pn.current_step_description = "Loading Fixtures"
        pn.current_step_number = 0
        fixtures: list[UsedFixture] = []
        phase_association: dict[UsedFixture, int] = {}
        phases: Counter[int] = Counter()

        for i in range(self._fixture_list.count()):
            item = self._fixture_list.item(i)
            if not isinstance(item, AnnotatedListWidgetItem):
                logger.error("Bug! All items should be annotated!")
                return False
            if not isinstance(item.annotated_data, UsedFixture):
                logger.error("Expected annotated data to be UsedFixtrue object.")
                return False
            if item.checkState() == Qt.CheckState.Checked:
                fixtures.append(item.annotated_data)

        pn.current_step_description = "Schedule Phases"
        pn.current_step_number += 1
        self._schedule_phases(fixtures, phase_association, phases)

        pn.current_step_description = "Write File"
        pn.current_step_number += 1
        self._write_csv_file(fixtures, phase_association, phases)

        pn.current_step_number += 1
        pn.close()

        return True

    def _write_csv_file(
        self, fixtures: list[UsedFixture], phase_association: dict[UsedFixture, int], phases: Counter[int]
    ) -> None:
        """Write a CSV file for a fixture list with its phase schedule."""
        fixtures.sort(key=lambda f: f.universe.id * 512 + f.start_index)
        with open(self._export_location_tb.text(), "w", newline="") as csv_file:
            logger.info("Exporting Fixtures as CSV to %s.", csv_file.name)
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(
                [
                    "Fixture Name",
                    "Fixture Type",
                    "Universe",
                    "Address",
                    "Phase",
                    "Fixture Power [W]",
                    "Total Phase Load [W]",
                ]
            )
            for fixture in fixtures:
                fixture_phase = phase_association[fixture]
                writer.writerow(
                    [
                        fixture.name_on_stage or fixture.name,
                        fixture.fixture_file,
                        str(fixture.universe.id),
                        str(fixture.start_index),
                        f"L{fixture_phase + 1}",
                        str(fixture.power),
                        str(phases[fixture_phase]),
                    ]
                )

    def _schedule_phases(
        self, fixtures: list[UsedFixture], phase_association: dict[UsedFixture, int], phases: Counter[int]
    ) -> None:
        """Distribute fixtures on the available power phases.

        Args:
            fixtures: The list of fixtures to use.
            phase_association: The mapping of fixtures to their phases. This dictionary will be filled in.
            phases: The load on each power phase in watts.

        """
        number_of_phases = self._number_phases_sb.value()
        fixtures.sort(key=lambda f: f.physical.power, reverse=True)
        for fixture in fixtures:
            selected_phase = 0
            for i in range(number_of_phases):
                if phases[i] < phases[selected_phase]:
                    selected_phase = i
            phase_association[fixture] = selected_phase
            phases[selected_phase] += fixture.power
            if fixture.power == 0:
                logger.warning(
                    "Fixture %s reported power requirement of %sW. This seams odd.", str(fixture), str(fixture.power)
                )
        for phase_index, phase_load in phases.items():
            if phase_load > 2400:
                logger.warning(
                    "Phase L%s exceeds 2.4kW. It totals to %sW. Please check that the phase is not overloaded. "
                    "Keep in mind larger initial currents!",
                    str(phase_index + 1),
                    str(phase_load),
                )
