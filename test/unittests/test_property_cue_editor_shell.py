"""Unit tests for the WP10 property-based cue editor shell."""

from __future__ import annotations

import gc
import importlib.util
import sys
import unittest
from logging import getLogger

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None

logger = getLogger(__name__)

_qapp = None


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create a shared QApplication so widgets can be instantiated in tests."""
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication
    _qapp = QApplication.instance() or QApplication(sys.argv)
    gc.disable()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    gc.enable()


def _make_scene():
    from model import BoardConfiguration, Scene
    show = BoardConfiguration()
    scene = Scene(0, "Test property-cue editor scene", show)
    show._add_scene(scene)
    return scene


@unittest.skipUnless(_HAS_PYSIDE, "Scene constructor requires PySide6")
class PropertyCueEditorShellTests(unittest.TestCase):

    def _make_filter(self):
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter
        scene = _make_scene()
        return PropertyBasedCueFilter(scene, "pcf_shell")

    def test_get_widget_returns_qwidget(self) -> None:
        from PySide6.QtWidgets import QWidget
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        widget = editor.get_widget()
        self.assertIsInstance(widget, QWidget)

    def test_cue_table_starts_empty(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        self.assertEqual(0, editor._cue_table.rowCount())

    def test_refresh_cue_table_adds_row(self) -> None:
        from model.virtual_filters.property_cues.model import PropertyCue, PropertyStep
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        f.property_model.cues.append(
            PropertyCue(
                name="Alpha",
                steps=[PropertyStep(name="s0", duration_40hz=40, assignments={})],
            ),
        )
        editor._refresh_cue_table()
        self.assertEqual(1, editor._cue_table.rowCount())
        self.assertEqual("1", editor._cue_table.item(0, 0).text())
        self.assertEqual("Alpha", editor._cue_table.item(0, 1).text())
        self.assertEqual("1", editor._cue_table.item(0, 2).text())

    def test_launch_wizard_with_empty_board_does_not_crash(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        original_selection = f.property_model.fixture_selection
        # Patch exec to avoid the wizard entering a Qt event loop; return 0 (rejected).
        from view.show_mode.editor.node_editor_widgets.property_cue_editor import wizard

        original_cls = wizard.FixtureSelectionWizard
        instances: list = []

        class _StubWizard(original_cls):
            def exec(self):  # type: ignore[override]
                instances.append(self)
                return 0

        wizard.FixtureSelectionWizard = _StubWizard
        try:
            editor._launch_wizard()
        finally:
            wizard.FixtureSelectionWizard = original_cls
        self.assertEqual(1, len(instances))
        self.assertIs(original_selection, f.property_model.fixture_selection)

    def test_configuration_roundtrip(self) -> None:
        from model.virtual_filters.property_cues.model import PropertyCue
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        f.property_model.cues.append(PropertyCue(name="Beta"))

        conf = editor._get_configuration()
        self.assertIn("cues-prop-data", conf)
        self.assertNotEqual("", conf["cues-prop-data"])

        g = self._make_filter()
        editor2 = PropertyCueEditor(f=g)
        editor2._load_configuration(conf)
        self.assertEqual(1, editor2._cue_table.rowCount())
        self.assertEqual("Beta", editor2._cue_table.item(0, 1).text())

    def test_add_cue_button_appends_cue_with_default_step(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        self.assertEqual(0, editor._cue_table.rowCount())
        editor._add_cue()
        self.assertEqual(1, len(f.property_model.cues))
        self.assertEqual("Cue 1", f.property_model.cues[0].name)
        self.assertEqual(1, len(f.property_model.cues[0].steps))
        self.assertEqual(1, editor._cue_table.rowCount())
        # Newly added cue should be selected.
        self.assertEqual(0, editor._cue_table.currentRow())

    def test_cue_settings_disabled_without_selection(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        # No cues -> per-cue widgets must be disabled.
        self.assertFalse(editor._end_action_combo.isEnabled())
        self.assertFalse(editor._restart_on_play_cb.isEnabled())
        self.assertFalse(editor._add_step_button.isEnabled())
        editor._add_cue()
        self.assertTrue(editor._end_action_combo.isEnabled())
        self.assertTrue(editor._restart_on_play_cb.isEnabled())
        self.assertTrue(editor._add_step_button.isEnabled())

    def test_end_action_combo_binds_to_selected_cue(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        editor._add_cue()
        editor._add_cue()
        editor._cue_table.selectRow(1)
        editor._end_action_combo.setCurrentText("next_cue")
        self.assertEqual("hold", f.property_model.cues[0].end_action)
        self.assertEqual("next_cue", f.property_model.cues[1].end_action)
        # Switching selection back to cue 0 must reflect its own values.
        editor._cue_table.selectRow(0)
        self.assertEqual("hold", editor._end_action_combo.currentText())

    def test_cue_selection_updates_step_tree(self) -> None:
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        editor._add_cue()
        editor._add_cue()
        editor._cue_table.selectRow(1)
        self.assertEqual(1, editor._step_tree._current_cue_index)
        editor._cue_table.selectRow(0)
        self.assertEqual(0, editor._step_tree._current_cue_index)

    def test_splitter_is_vertical_and_property_pane_has_min_height(self) -> None:
        from PySide6.QtCore import Qt
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        self.assertEqual(Qt.Orientation.Vertical, editor._splitter.orientation())
        self.assertGreaterEqual(editor._property_pane.minimumHeight(), 100)


@unittest.skipUnless(_HAS_PYSIDE, "FilterTypeEnumeration import is cheap but keep guard parity")
class PropertyBasedCuesNodeRegistrationTests(unittest.TestCase):

    def test_type_to_node_mapping(self) -> None:
        from model.filter import FilterTypeEnumeration
        from view.show_mode.editor.nodes.impl.effects import PropertyBasedCuesNode
        from view.show_mode.editor.nodes.type_to_node_dict import type_to_node

        self.assertIn(FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES, type_to_node)
        self.assertEqual(
            PropertyBasedCuesNode.nodeName,
            type_to_node[FilterTypeEnumeration.VFILTER_PROPERTY_BASED_CUES],
        )
        self.assertEqual("Property Cues", PropertyBasedCuesNode.nodeName)


if __name__ == "__main__":
    unittest.main()
