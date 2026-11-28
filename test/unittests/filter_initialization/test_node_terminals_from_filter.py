"""Tests for deriving node terminals from filter signatures."""

from __future__ import annotations

import unittest

from ._qapp_setup import setup_qapp, teardown_qapp


def setUpModule() -> None:  # noqa: N802 - unittest hook naming
    """Create the shared ``QApplication`` and freeze cyclic GC for this module."""
    setup_qapp()


def tearDownModule() -> None:  # noqa: N802 - unittest hook naming
    """Re-enable cyclic GC once this module's tests have finished."""
    teardown_qapp()


class NodeTerminalsFromFilterTests(unittest.TestCase):
    """When a node passes ``terminals=None``, the base derives terminals from the filter.

    PR 1 removes the explicit ``terminals=`` arg from the migrated adapter nodes, so this
    test guards that the pyqtgraph Node ends up with the exact terminal set that the
    filter's subclass declared.
    """

    def _make_scene(self):
        from model import BoardConfiguration, Scene

        show = BoardConfiguration()
        scene = Scene(0, "Test scene", show)
        show._add_scene(scene)
        return scene

    def test_adapter_node_derives_terminals_from_filter(self) -> None:
        """Adapter nodes with no explicit terminals must derive them from the filter's I/O signature."""
        from view.show_mode.editor.nodes.impl.adapters import AdapterColorToRGBWANode

        scene = self._make_scene()
        node = AdapterColorToRGBWANode(model=scene, name="rgbwa")
        # pyqtgraph exposes inputs/outputs dicts
        self.assertEqual(set(node.inputs().keys()), {"value"})
        self.assertEqual(set(node.outputs().keys()), {"r", "g", "b", "w", "a"})
        self.assertFalse(node.filter.configuration_supported)
