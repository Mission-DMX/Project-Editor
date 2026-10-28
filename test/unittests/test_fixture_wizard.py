"""Headless tests for the property-cue fixture-selection wizard (WP6).

The entire module is skipped when PySide6 is not importable so the pure
Python helpers can still be exercised in environments that lack Qt.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from unittest.mock import MagicMock

_PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None


_qapp = None


def _ensure_qapp():
    global _qapp
    if not _PYSIDE6_AVAILABLE:
        return None
    from PySide6.QtWidgets import QApplication

    _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


def setUpModule() -> None:  # noqa: N802 — unittest hook naming
    """Spin up a shared QApplication for every test that imports Qt widgets."""
    _ensure_qapp()


@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 required")
class CapabilityDiscoveryTests(unittest.TestCase):
    """Pure-Python coverage of ``_capability_discovery.discover_capabilities``.

    Fixtures are built as :class:`MagicMock` because a real ``UsedFixture``
    requires a full ``BoardConfiguration``, an ``OflFixture`` and a wired
    broadcaster. The wizard only touches ``fixture_channels``,
    ``channel_template`` and the capability types, which are easy to stub.
    """

    def _make_fixture_with_capabilities(self, pairs):
        """Build a fixture mock from ``[(channel_name, capability_type), ...]`` pairs."""
        channels = []
        for channel_name, cap_type in pairs:
            capability = MagicMock()
            capability.type = cap_type
            template = MagicMock()
            template.get_capabilities.return_value = [capability]
            channel = MagicMock()
            channel.name = channel_name
            channel.channel_template = template
            channels.append(channel)
        fixture = MagicMock()
        fixture.fixture_channels = tuple(channels)
        return fixture

    def test_capability_discovery_pan_tilt_maps_to_position(self) -> None:
        from model.ofl.ofl_fixture import CapabilityType
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard._capability_discovery import (
            discover_capabilities,
        )

        fixture = self._make_fixture_with_capabilities(
            [("Pan", CapabilityType.PAN), ("Tilt", CapabilityType.TILT)]
        )
        self.assertEqual(discover_capabilities([fixture]), {EnabledCapability.POSITION})

    def test_capability_discovery_colour_only(self) -> None:
        from model.ofl.ofl_fixture import CapabilityType
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard._capability_discovery import (
            discover_capabilities,
        )

        fixture = self._make_fixture_with_capabilities(
            [
                ("Red", CapabilityType.COLOR_INTENSITY),
                ("Green", CapabilityType.COLOR_INTENSITY),
                ("Blue", CapabilityType.COLOR_INTENSITY),
            ]
        )
        self.assertEqual(discover_capabilities([fixture]), {EnabledCapability.COLOUR})

    def test_capability_discovery_gobo_wheel_from_slot_types(self) -> None:
        """A wheel whose slots are typed GOBO should surface GOBO regardless of name."""
        from model.ofl.ofl_fixture import WheelSlotType
        from model.virtual_filters.property_cues.model.fixture_selection import EnabledCapability
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard._capability_discovery import (
            discover_capabilities,
        )

        colour_slot = MagicMock(); colour_slot.type = WheelSlotType.COLOR
        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        colour_wheel = MagicMock(); colour_wheel.slots = [colour_slot]
        gobo_wheel = MagicMock(); gobo_wheel.slots = [gobo_slot]

        fixture_colour = self._make_fixture_with_capabilities([])
        fixture_colour._fixture = MagicMock(); fixture_colour._fixture.wheels = {"Colour Wheel": colour_wheel}
        fixture_gobo = self._make_fixture_with_capabilities([])
        fixture_gobo._fixture = MagicMock(); fixture_gobo._fixture.wheels = {"Gobo Wheel": gobo_wheel}
        fixture_without_wheel = self._make_fixture_with_capabilities([])
        fixture_without_wheel._fixture = MagicMock(); fixture_without_wheel._fixture.wheels = {}

        self.assertEqual(discover_capabilities([fixture_colour]), {EnabledCapability.COLOUR})
        self.assertEqual(discover_capabilities([fixture_gobo]), {EnabledCapability.GOBO})
        self.assertEqual(discover_capabilities([fixture_without_wheel]), set())

    def test_gobo_wheels_of_returns_only_gobo_wheels(self) -> None:
        from model.ofl.ofl_fixture import WheelSlotType
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard._capability_discovery import (
            gobo_wheels_of,
        )

        colour_slot = MagicMock(); colour_slot.type = WheelSlotType.COLOR
        gobo_slot = MagicMock(); gobo_slot.type = WheelSlotType.GOBO
        colour_wheel = MagicMock(); colour_wheel.slots = [colour_slot]
        gobo_wheel = MagicMock(); gobo_wheel.slots = [gobo_slot]
        fixture = MagicMock()
        fixture._fixture = MagicMock(); fixture._fixture.wheels = {
            "Colour Wheel": colour_wheel, "Gobo Wheel": gobo_wheel,
        }
        wheels = gobo_wheels_of(fixture)
        self.assertEqual([n for n, _ in wheels], ["Gobo Wheel"])

    def test_capability_discovery_unknown_type_skipped(self) -> None:
        from model.ofl.ofl_fixture import CapabilityType
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard._capability_discovery import (
            discover_capabilities,
        )

        fixture = self._make_fixture_with_capabilities(
            [("Fog Out", CapabilityType.FOG)]
        )
        self.assertEqual(discover_capabilities([fixture]), set())


@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 required")
class WizardHeadlessTests(unittest.TestCase):
    """Round-trip and data-loss checks that drive the wizard without exec()."""

    def setUp(self) -> None:
        _ensure_qapp()

    def _make_board(self, fixtures):
        board = MagicMock()
        board.fixtures = list(fixtures)
        board.stage_config = None
        return board

    def _make_fixture_stub(self, uuid: str, name: str = "F"):
        from model.ofl.ofl_fixture import CapabilityType

        fixture = MagicMock()
        fixture.uuid = uuid
        fixture.name = name
        fixture.name_on_stage = name
        fixture.short_name = name
        fixture.universe_id = 1
        fixture.start_index = 0
        capability = MagicMock()
        capability.type = CapabilityType.COLOR_INTENSITY
        template = MagicMock()
        template.get_capabilities.return_value = [capability]
        channel = MagicMock()
        channel.name = "Red"
        channel.channel_template = template
        fixture.fixture_channels = (channel,)
        return fixture

    def test_wizard_round_trips_selection(self) -> None:
        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard import (
            FixtureSelectionWizard,
        )

        fixture_a = self._make_fixture_stub("fixture-a", "A")
        fixture_b = self._make_fixture_stub("fixture-b", "B")
        board = self._make_board([fixture_a, fixture_b])

        initial = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="fixture-a"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="fixture-b"),
            ],
            enabled_capabilities={EnabledCapability.COLOUR},
        )

        wizard = FixtureSelectionWizard(board, initial=initial)
        # Advance to the capability page so initializePage runs.
        wizard.restart()
        wizard.next()
        self.assertIs(wizard.currentPage(), wizard._capability_page)  # type: ignore[attr-defined]
        # Accept without changing anything.
        wizard.accept()

        result = wizard.result_selection()
        self.assertIsNotNone(result)
        self.assertEqual(
            {(e.kind, e.id) for e in result.entries},
            {(e.kind, e.id) for e in initial.entries},
        )
        self.assertEqual(result.enabled_capabilities, initial.enabled_capabilities)

    def test_wizard_warns_on_data_loss(self) -> None:
        from PySide6.QtWidgets import QMessageBox

        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.wizard import (
            FixtureSelectionWizard,
        )

        fixture_a = self._make_fixture_stub("fixture-a", "A")
        fixture_b = self._make_fixture_stub("fixture-b", "B")
        board = self._make_board([fixture_a, fixture_b])

        initial = FixtureSelection(
            entries=[
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="fixture-a"),
                FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="fixture-b"),
            ],
            enabled_capabilities={EnabledCapability.COLOUR},
        )

        wizard = FixtureSelectionWizard(board, initial=initial)
        # Uncheck fixture-b on the picker page.
        picker = wizard._picker_page  # type: ignore[attr-defined]
        from PySide6.QtCore import Qt

        for i in range(picker._fixture_root.childCount()):  # type: ignore[attr-defined]
            child = picker._fixture_root.child(i)  # type: ignore[attr-defined]
            entry = child.data(0, Qt.ItemDataRole.UserRole + 1)
            if entry is not None and entry.id == "fixture-b":
                child.setCheckState(0, Qt.CheckState.Unchecked)

        # Intercept the QMessageBox by patching .show() to capture self.
        captured: dict[str, QMessageBox] = {}
        original_show = QMessageBox.show

        def spy_show(self: QMessageBox) -> None:  # noqa: ANN001
            captured["box"] = self
            original_show(self)

        QMessageBox.show = spy_show  # type: ignore[method-assign]
        try:
            wizard.accept()
        finally:
            QMessageBox.show = original_show  # type: ignore[method-assign]

        self.assertIn("box", captured, "Expected a QMessageBox to be shown on data loss.")
        text = captured["box"].text()
        self.assertIn("lost", text.lower())
        # Verify we captured a reference on self so Qt couldn't GC it; must be checked
        # before dismissing the dialog because the ``finished`` handler nulls it.
        self.assertIsNotNone(wizard._msgbox)  # type: ignore[attr-defined]
        self.assertIs(wizard._msgbox, captured["box"])  # type: ignore[attr-defined]
        # Reject the dialog so the test leaves no leaks.
        captured["box"].reject()


if __name__ == "__main__":
    unittest.main()
