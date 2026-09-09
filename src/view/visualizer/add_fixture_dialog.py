"""Contains stage editor's AddFixtureDialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from model.visualizer.stage.model_entries import TRUSS_VARIANTS
from model.visualizer.stage.stage_config import make_unique_name

if TYPE_CHECKING:
    from model.ofl.fixture import UsedFixture


def _fixture_label(fix: UsedFixture) -> str:
    """Build a display label: ``[TAG] Name @ U{u}/CH{start} ({n}ch)``."""
    try:
        cats = fix._fixture.categories
        if "Moving Head" in cats:
            tag = "[MH]"
        elif any(c in cats for c in ("Color Changer", "Blinder", "Pixel Bar")):
            tag = "[RGB]"
        else:
            tag = "[" + cats[0] + "]" if cats else "[?]"
    except Exception:
        tag = ""
    name = fix.name_on_stage or fix.name or fix.short_name or "?"
    return f"{tag} {name} @ U{fix.universe_id}/CH{fix.start_index} ({fix.channel_length}ch)"


class AddFixtureDialog(QtWidgets.QDialog):
    """Dialog for adding a new fixture to the stage."""

    def __init__(self,
                 existing_names: list[str],
                 used_fixtures: list[UsedFixture] | None = None,
                 parent: QtWidgets.QWidget | None = None) -> None:
        """Initialize the dialog.

        It guarantees that the entered name is unique.

        Args:
            existing_names: Existing names, which should be avoided.
            used_fixtures: Fixtures to choose from.
            parent: Parent widget.

        """
        super().__init__(parent)
        self.setWindowTitle("Add Fixture")
        self.setModal(True)
        self.setMinimumWidth(380)
        self._existing_names = existing_names or []
        self._used_fixtures = used_fixtures or []

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        layout.addLayout(form)

        # Category selector
        self._category_combo = QtWidgets.QComboBox()
        self._category_combo.addItems(["Truss", "Moving Head"])
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        form.addRow("Fixture:", self._category_combo)

        # Truss variant selector
        self._variant_label = QtWidgets.QLabel("Type:")
        self._variant_combo = QtWidgets.QComboBox()
        self._variant_combo.addItems(list(TRUSS_VARIANTS.keys()))
        self._variant_combo.currentIndexChanged.connect(self._update_suggested_name)
        form.addRow(self._variant_label, self._variant_combo)

        # DMX device selector
        self._device_label = QtWidgets.QLabel("Device:")
        self._device_combo = QtWidgets.QComboBox()
        self._device_combo.addItem("(None)", None)
        for fix in self._used_fixtures:
            self._device_combo.addItem(_fixture_label(fix), fix)
        form.addRow(self._device_label, self._device_combo)

        # Name input
        self._name_edit = QtWidgets.QLineEdit()
        form.addRow("Name:", self._name_edit)

        # OK / Cancel buttons
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Initialize visibility
        self._on_category_changed()

    def _on_category_changed(self) -> None:
        """Show/hide category-specific controls."""
        is_truss = self._category_combo.currentText() == "Truss"
        self._variant_combo.setVisible(is_truss)
        self._variant_label.setVisible(is_truss)
        is_mh = self._category_combo.currentText() == "Moving Head"
        self._device_combo.setVisible(is_mh)
        self._device_label.setVisible(is_mh)
        self._update_suggested_name()

    def _update_suggested_name(self) -> None:
        """Auto-generate a unique name suggestion as placeholder text."""
        base = self._get_base_name()
        candidate = make_unique_name(base, self._existing_names)
        self._name_edit.setPlaceholderText(candidate)

    def _get_base_name(self) -> str:
        if self._category_combo.currentText() == "Truss":
            return f"Truss {self._variant_combo.currentText()}"
        return "Moving Head"

    def selected_fixture_key(self) -> str:
        """Return the internal fixture key for the selected type."""
        if self._category_combo.currentText() == "Truss":
            v = self._variant_combo.currentText()
            return TRUSS_VARIANTS.get(v, "truss_default")
        return "moving_head"

    def selected_name(self) -> str:
        """Return the user-entered name (or the auto-generated placeholder)."""
        text = self._name_edit.text().strip()
        return text or self._name_edit.placeholderText()

    def selected_device(self) -> UsedFixture | None:
        """Return the selected UsedFixture for DMX linking, or None."""
        return self._device_combo.currentData()
