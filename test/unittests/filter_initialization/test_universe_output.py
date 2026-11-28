"""Tests for the universe output filter."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class UniverseOutputTests(unittest.TestCase):
    """Per-type assertions for the UniverseOutput subclass migrated in PR 10.

    The universe filter is dynamic: every non-``"universe"`` config key becomes an 8-bit
    input terminal. The node-side ``UniverseNode`` keeps interactive add/remove behaviour.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_empty_config_yields_no_inputs(self) -> None:
        """A UniverseOutput with no config has empty I/O dicts."""
        from model.filter import FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene, filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT, filter_id="u"
        )
        self.assertEqual(f.in_data_types, {})
        self.assertEqual(f.out_data_types, {})

    def test_configs_populate_inputs_excluding_universe_key(self) -> None:
        """Every non-``universe`` config entry becomes an 8-bit input terminal."""
        from model.filter import DataType, FilterTypeEnumeration
        from model.filters.factory import construct_filter_instance

        scene = self._make_scene()
        f = construct_filter_instance(
            scene=scene,
            filter_type=FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT,
            filter_id="u",
            filter_configurations={"universe": "3", "input_1": "0", "fixture_a": "17"},
        )
        self.assertEqual(f.filter_configurations["universe"], "3")
        self.assertEqual(set(f.in_data_types.keys()), {"input_1", "fixture_a"})
        for key in ("input_1", "fixture_a"):
            self.assertEqual(f.in_data_types[key], DataType.DT_8_BIT)
            self.assertEqual(f.default_values[key], "0")

    def test_fresh_universe_node_seeds_default_universe_id_and_input(self) -> None:
        """A new UniverseNode seeds universe=1 and one default input_1 terminal."""
        from view.show_mode.editor.nodes.impl.universenode import UniverseNode

        scene = self._make_scene()
        node = UniverseNode(model=scene, name="Universe0")
        self.assertEqual(node.filter.filter_configurations["universe"], "1")
        self.assertEqual(node.filter.filter_configurations["input_1"], "0")
        self.assertEqual(set(node.inputs().keys()), {"input_1"})

    def test_universe_node_add_input_updates_model_and_terminals(self) -> None:
        """``UniverseNode.addInput`` adds a new input terminal and syncs the backing model."""
        from view.show_mode.editor.nodes.impl.universenode import UniverseNode

        scene = self._make_scene()
        node = UniverseNode(model=scene, name="Universe0")
        node.addInput()
        self.assertIn("input_2", node.inputs())
        self.assertEqual(node.filter.filter_configurations["input_2"], "1")
        self.assertEqual(node.filter.in_data_types["input_2"].value, 1)  # DT_8_BIT

    def test_universe_node_remove_terminal_clears_config_and_model(self) -> None:
        """Removing a universe node input terminal drops it from configs and in_data_types."""
        from view.show_mode.editor.nodes.impl.universenode import UniverseNode

        scene = self._make_scene()
        node = UniverseNode(model=scene, name="Universe0")
        node.addInput()  # adds input_2
        self.assertIn("input_2", node.filter.filter_configurations)
        node.removeTerminal(node.inputs()["input_2"])
        self.assertNotIn("input_2", node.filter.filter_configurations)
        self.assertNotIn("input_2", node.filter.in_data_types)
