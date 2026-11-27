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
    """Re-enable garbage collection after the module-level tests have finished."""
    gc.enable()


def _make_scene():
    """Return a fresh Scene bound to a BoardConfiguration for use in editor tests."""
    from model import BoardConfiguration, Scene
    show = BoardConfiguration()
    scene = Scene(0, "Test property-cue editor scene", show)
    show._add_scene(scene)
    return scene


@unittest.skipUnless(_HAS_PYSIDE, "Scene constructor requires PySide6")
class PropertyCueEditorShellTests(unittest.TestCase):
    """Verify behavior of the property-based cue editor shell widget."""

    def _make_filter(self):
        """Return a new PropertyBasedCueFilter attached to a fresh scene."""
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter
        scene = _make_scene()
        return PropertyBasedCueFilter(scene, "pcf_shell")

    def test_get_widget_returns_qwidget(self) -> None:
        """Verify the editor's get_widget returns a QWidget instance."""
        from PySide6.QtWidgets import QWidget
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        widget = editor.get_widget()
        self.assertIsInstance(widget, QWidget)

    def test_cue_table_starts_empty(self) -> None:
        """Verify the cue table has no rows for a freshly constructed editor."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        self.assertEqual(0, editor._cue_table.rowCount())

    def test_refresh_cue_table_adds_row(self) -> None:
        """Verify refreshing the cue table adds a row reflecting a newly added cue."""
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
        """Verify launching the fixture-selection wizard with no fixtures does not crash."""
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
        """Verify saving and loading the editor configuration preserves cue data."""
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

    def test_mutations_drop_vfilter_compile_cache(self) -> None:
        """Regression (L10): model mutations must invalidate the vfilter's compile cache.

        Before L10 only :meth:`_rebuild_io` (dialog close) and ``deserialize``
        cleared ``PropertyBasedCueFilter._last_compile``, so starting the
        preview after an edit replayed the pre-edit timeline. Every mutator
        in the editor shell now routes through :meth:`_invalidate_cache`.
        """
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )
        f = self._make_filter()
        editor = PropertyCueEditor(f=f)

        def _prime_cache() -> None:
            f._last_compile = object()

        _prime_cache()
        editor._add_cue()
        self.assertIsNone(f._last_compile, "add_cue must invalidate compile cache")

        _prime_cache()
        editor._add_step()
        self.assertIsNone(f._last_compile, "add_step must invalidate compile cache")

        _prime_cache()
        editor._persistence_toggled(True)
        self.assertIsNone(f._last_compile, "persistence toggle must invalidate compile cache")

        # end_action / restart_on_play mutate the selected cue; the above
        # ``_add_step`` called ``_refresh_cue_table`` which clears the
        # selection, so re-select before testing per-cue mutators.
        editor._cue_table.selectRow(0)
        _prime_cache()
        editor._end_action_changed("START_AGAIN")
        self.assertIsNone(f._last_compile, "end_action change must invalidate compile cache")

        _prime_cache()
        editor._restart_on_play_toggled(True)
        self.assertIsNone(f._last_compile, "restart_on_play change must invalidate compile cache")

    def test_delete_cue_removes_from_model(self) -> None:
        """Regression (L19): the delete-cue button removes the selected cue."""
        from model.virtual_filters.property_cues.model import PropertyCue, PropertyStep
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )
        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        for name in ("A", "B", "C"):
            f.property_model.cues.append(
                PropertyCue(name=name, steps=[PropertyStep(name="s0", duration_40hz=40)]),
            )
        editor._refresh_cue_table()
        editor._cue_table.selectRow(1)
        editor._delete_cue()
        self.assertEqual([c.name for c in f.property_model.cues], ["A", "C"])

    def test_move_cue_swaps_order(self) -> None:
        """Regression (L19): move-cue reorders the cues in the model."""
        from model.virtual_filters.property_cues.model import PropertyCue, PropertyStep
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )
        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        for name in ("A", "B", "C"):
            f.property_model.cues.append(
                PropertyCue(name=name, steps=[PropertyStep(name="s0", duration_40hz=40)]),
            )
        editor._refresh_cue_table()
        editor._cue_table.selectRow(0)
        editor._move_cue(1)
        self.assertEqual([c.name for c in f.property_model.cues], ["B", "A", "C"])

    def test_rename_cue_via_table_edit(self) -> None:
        """Regression (L19): editing the Name cell writes the new name back to the model."""
        from model.virtual_filters.property_cues.model import PropertyCue, PropertyStep
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )
        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        f.property_model.cues.append(
            PropertyCue(name="Old", steps=[PropertyStep(name="s0", duration_40hz=40)]),
        )
        editor._refresh_cue_table()
        editor._cue_table.item(0, 1).setText("Renamed")
        self.assertEqual("Renamed", f.property_model.cues[0].name)

    def test_add_cue_button_appends_cue_with_default_step(self) -> None:
        """Verify adding a cue creates a default step and selects the new row."""
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
        """Verify per-cue widgets are disabled when no cue is selected and enabled once one exists."""
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
        """Verify the end-action combo updates only the currently selected cue's end action."""
        from model.filter_data.cues.cue import EndAction
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        editor._add_cue()
        editor._add_cue()
        editor._cue_table.selectRow(1)
        editor._end_action_combo.setCurrentText("NEXT")
        self.assertEqual(EndAction.HOLD, f.property_model.cues[0].end_action)
        self.assertEqual(EndAction.NEXT, f.property_model.cues[1].end_action)
        # Switching selection back to cue 0 must reflect its own values.
        editor._cue_table.selectRow(0)
        self.assertEqual("HOLD", editor._end_action_combo.currentText())

    def test_cue_selection_updates_step_tree(self) -> None:
        """Verify selecting a different cue row refreshes the step tree's current cue index."""
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
        """Verify the editor's splitter is vertical and the property pane has a sensible minimum height."""
        from PySide6.QtCore import Qt
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        self.assertEqual(Qt.Orientation.Vertical, editor._splitter.orientation())
        # The pane's minimum tracks the tallest property-editor tab (computed at
        # runtime) and is at least 100 px so very short editors still get space.
        expected = max(100, editor._property_pane.recommended_minimum_height())
        self.assertEqual(expected, editor._property_pane.minimumHeight())
        self.assertGreaterEqual(editor._property_pane.minimumHeight(), 100)

    def test_parent_closed_triggers_node_terminal_sync(self) -> None:
        """Verify parent_closed propagates to update_node_after_settings_changed on the node.

        The super chain calls ``update_node_after_settings_changed`` on the
        node, which in turn runs ``_rebuild_io`` and syncs pyqtgraph terminals
        with the vfilter's refreshed ``out_data_types``.
        """
        from unittest.mock import MagicMock
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import (
            PropertyCueEditor,
        )

        f = self._make_filter()
        editor = PropertyCueEditor(f=f)
        fake_node = MagicMock()
        editor.parent_closed(fake_node)
        fake_node.update_node_after_settings_changed.assert_called()


@unittest.skipUnless(_HAS_PYSIDE, "FilterTypeEnumeration import is cheap but keep guard parity")
class PropertyBasedCuesNodeRegistrationTests(unittest.TestCase):
    """Verify the PropertyBasedCuesNode is registered against the right filter type."""

    def test_type_to_node_mapping(self) -> None:
        """Verify the VFILTER_PROPERTY_BASED_CUES filter type maps to PropertyBasedCuesNode."""
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
