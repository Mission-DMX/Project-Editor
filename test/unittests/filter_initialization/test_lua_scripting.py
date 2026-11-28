"""Tests for the Lua scripting filter subclass."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class LuaScriptingTests(unittest.TestCase):
    """Per-type assertions for the Lua scripting subclass migrated in PR 8.

    Also covers the base ``update_node_after_settings_changed`` promotion: the Lua filter is
    the first dynamic-I/O subclass in the hierarchy, so its node relies on the base's
    generic rebuild+sync behaviour instead of a custom override.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_default_mappings_and_script_applied(self) -> None:
        """Default Lua filter seeds empty mappings, a stub script, and empty I/O dicts."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(scene=scene, filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA, filter_id="lua")
        self.assertEqual(f.filter_configurations["in_mapping"], "")
        self.assertEqual(f.filter_configurations["out_mapping"], "")
        self.assertIn("function update()", f.initial_parameters["script"])
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})

    def test_mapping_parsing_populates_io(self) -> None:
        """Parsing ``in_mapping`` / ``out_mapping`` configs populates typed Lua I/O ports."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA,
            filter_id="lua",
            filter_configurations={"in_mapping": "a:8bit;b:color", "out_mapping": "y:float;z:16bit"},
        )
        self.assertEqual(f.in_data_types, {"a": DataType.DT_8_BIT, "b": DataType.DT_COLOR})
        self.assertEqual(f.out_data_types, {"y": DataType.DT_DOUBLE, "z": DataType.DT_16_BIT})

    def test_malformed_entries_skipped_and_do_not_raise(self) -> None:
        """A corrupt show file must still load; bad entries are logged and dropped."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA,
            filter_id="lua",
            filter_configurations={
                # valid, no-separator, empty-name, unknown-dtype, duplicate-name
                "in_mapping": "good:8bit;badentry;:nokey;odd:unknown_dtype;good:16bit",
                "out_mapping": "other:color",
            },
        )
        # Only the first "good" entry survived; its data type is 8bit (duplicate ignored)
        self.assertEqual(f.in_data_types, {"good": DataType.DT_8_BIT})
        self.assertEqual(f.out_data_types, {"other": DataType.DT_COLOR})

    def test_update_filter_configuration_rebuilds_terminals(self) -> None:
        """Writing a new mapping via update_filter_configuration re-runs the parse."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_SCRIPTING_LUA, filter_id="lua"
        )
        self.assertEqual(f.out_data_types, {})
        f.update_filter_configuration("out_mapping", "p:float")
        self.assertEqual(f.out_data_types, {"p": DataType.DT_DOUBLE})

    def test_node_derives_lua_terminals_and_syncs_on_settings_change(self) -> None:
        """End-to-end: construct a Lua node, mutate config directly, call base rebuild+sync."""
        from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode

        scene = self._make_scene()
        # Pre-populate the scene filter path through node to simulate interactive creation.
        node = LuaFilterNode(model=scene, name="lua")
        self.assertEqual(set(node.inputs().keys()), set())
        self.assertEqual(set(node.outputs().keys()), set())
        # Simulate the FilterSettingsItem flow: dict mutation + update_node_after_settings_changed.
        node.filter.filter_configurations["in_mapping"] = "a:8bit"
        node.filter.filter_configurations["out_mapping"] = "y:color"
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.inputs().keys()), {"a"})
        self.assertEqual(set(node.outputs().keys()), {"y"})
        # Removing a channel via a new mapping should remove the terminal from pyqtgraph.
        node.filter.filter_configurations["out_mapping"] = ""
        node.update_node_after_settings_changed()
        self.assertEqual(set(node.outputs().keys()), set())

    def test_settings_change_preserves_unrelated_connections(self) -> None:
        """A terminal diff must only sever connections on removed terminals.

        Connections on terminals that survive the diff (same name, both before and after)
        must stay intact — both at the pyqtgraph level and at the model's channel_links
        level. This guards against a naive "clear all then re-add" implementation that
        would silently drop user-made wiring.
        """
        from unittest.mock import MagicMock

        from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode

        scene = self._make_scene()
        src = LuaFilterNode(model=scene, name="src")
        src.filter.filter_configurations["out_mapping"] = "a:8bit;b:8bit;c:8bit"
        src.update_node_after_settings_changed()

        dst = LuaFilterNode(model=scene, name="dst")
        dst.filter.filter_configurations["in_mapping"] = "xa:8bit;xb:8bit;xc:8bit"
        dst.update_node_after_settings_changed()

        # Install three connections without the pyqtgraph graphics stack. A mock stands in
        # for the ConnectionItem; Terminal.disconnectFrom only requires ``.close()`` on it,
        # and the terminals' ``connected()`` / ``disconnected()`` hooks drive the model-side
        # channel_links updates we care about.
        def connect(out_term, in_term) -> None:
            item = MagicMock()
            out_term._connections[in_term] = item
            in_term._connections[out_term] = item
            out_term.connected(in_term)
            in_term.connected(out_term)

        connect(src.outputs()["a"], dst.inputs()["xa"])
        connect(src.outputs()["b"], dst.inputs()["xb"])
        connect(src.outputs()["c"], dst.inputs()["xc"])
        self.assertEqual(
            dict(dst.filter.channel_links), {"xa": "src:a", "xb": "src:b", "xc": "src:c"}
        )

        a_term_before = src.outputs()["a"]
        c_term_before = src.outputs()["c"]

        # Remove only the middle output. 'a' and 'c' must survive without disturbance.
        src.filter.filter_configurations["out_mapping"] = "a:8bit;c:8bit"
        src.update_node_after_settings_changed()

        self.assertEqual(set(src.outputs().keys()), {"a", "c"})
        # Terminal objects for surviving ports are preserved — the diff did not re-create them.
        self.assertIs(src.outputs()["a"], a_term_before)
        self.assertIs(src.outputs()["c"], c_term_before)
        # Model-side channel_links reflect the severed connection on xb and keep the rest.
        self.assertEqual(dst.filter.channel_links["xa"], "src:a")
        self.assertEqual(dst.filter.channel_links["xc"], "src:c")
        self.assertEqual(dst.filter.channel_links["xb"], "")
        # pyqtgraph-side connections: xa and xc still linked, xb severed.
        self.assertEqual(len(dst.inputs()["xa"].connections()), 1)
        self.assertEqual(len(dst.inputs()["xc"].connections()), 1)
        self.assertEqual(len(dst.inputs()["xb"].connections()), 0)

    def test_settings_change_adds_new_terminal_without_touching_existing_connections(self) -> None:
        """Adding a brand-new terminal must leave previously-wired terminals alone."""
        from unittest.mock import MagicMock

        from view.show_mode.editor.nodes.impl.scripting import LuaFilterNode

        scene = self._make_scene()
        src = LuaFilterNode(model=scene, name="src")
        src.filter.filter_configurations["out_mapping"] = "a:8bit"
        src.update_node_after_settings_changed()

        dst = LuaFilterNode(model=scene, name="dst")
        dst.filter.filter_configurations["in_mapping"] = "xa:8bit"
        dst.update_node_after_settings_changed()

        item = MagicMock()
        src.outputs()["a"]._connections[dst.inputs()["xa"]] = item
        dst.inputs()["xa"]._connections[src.outputs()["a"]] = item
        src.outputs()["a"].connected(dst.inputs()["xa"])
        dst.inputs()["xa"].connected(src.outputs()["a"])

        a_term_before = src.outputs()["a"]

        # Add a new output alongside the existing one.
        src.filter.filter_configurations["out_mapping"] = "a:8bit;new_output:color"
        src.update_node_after_settings_changed()

        self.assertEqual(set(src.outputs().keys()), {"a", "new_output"})
        self.assertIs(src.outputs()["a"], a_term_before)
        self.assertEqual(dst.filter.channel_links["xa"], "src:a")
        self.assertEqual(len(dst.inputs()["xa"].connections()), 1)
