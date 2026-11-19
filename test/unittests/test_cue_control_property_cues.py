"""Coverage for ``CueControlUIWidget`` wired against a property-based cue filter.

Before the change the show-mode cue control widget only supported the
legacy ``CueFilter`` -- it narrowed to ``isinstance(self._filter,
CueFilter)`` for subscription and loaded cue names through
``CueFilterModel.load_from_configuration``, which expects the
``cuelist``/``mapping`` config shape the property-based vfilter never
emits. Pointing the widget at a ``PropertyBasedCueFilter`` therefore
quietly produced an empty cue list and swallowed every play/pause/next
command because the fish forwarder wasn't registered.

The widget now subscribes against the shared ``PreviewFilter`` base
(``CueFilter`` and ``PropertyBasedCueFilter`` both carry
``linked_ui_widgets`` there) and reads cue names straight off
``PropertyBasedCueFilter.property_model.cues``.
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
    """Spin up a shared QApplication because the widget creates QObjects on init."""
    _ensure_qapp()


@unittest.skipUnless(_PYSIDE6_AVAILABLE, "PySide6 required")
class CueControlPropertyCueTest(unittest.TestCase):
    """Drive the widget against mocked ``CueFilter`` and ``PropertyBasedCueFilter`` flavours."""

    def _build_widget(self):
        """Instantiate ``CueControlUIWidget`` with a stubbed parent UI page."""
        from view.show_mode.show_ui_widgets.cue_control import CueControlUIWidget

        parent = MagicMock()
        parent.scene = MagicMock()
        return CueControlUIWidget(parent, {})

    def test_update_model_reads_cues_off_property_based_cue_filter(self) -> None:
        """Names come straight off ``property_model.cues`` -- no ``CueFilterModel``."""
        from model.virtual_filters.property_cues.model.property_cue import PropertyCue
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        f = MagicMock(spec=PropertyBasedCueFilter)
        f.filter_id = "Property Cues.0"
        model = MagicMock()
        model.cues = [PropertyCue(name="Intro"), PropertyCue(name="Verse")]
        f.property_model = model

        widget = self._build_widget()
        widget._filter = f

        widget.update_model(clear_model=True)

        self.assertEqual([("Intro", 0), ("Verse", 1)], widget._cues)
        # Loading a property-based cue filter must not materialise a
        # CueFilterModel -- that path is wrong for this flavour and would
        # dirty up the migration helper.
        self.assertIsNone(widget._model)

    def test_update_model_still_uses_cuefiltermodel_for_cue_filter(self) -> None:
        """Legacy path untouched -- the CueFilter branch still loads via configurations."""
        from model.virtual_filters.cue_vfilter import CueFilter

        f = MagicMock(spec=CueFilter)
        f.filter_id = "Cues.0"
        f.filter_configurations = {
            "mapping": "colour:color",
            "end_handling": "hold",
            "cuelist": "0.0:0.0,1.0,1.0@lin#hold#do_nothing#Legacy Cue",
        }

        widget = self._build_widget()
        widget._filter = f

        widget.update_model(clear_model=False)

        self.assertEqual(1, len(widget._cues))
        self.assertEqual(("Legacy Cue", 0), widget._cues[0])
        # ``_model`` must stay populated so ``_migrate_name_list`` can still
        # mutate it when the showfile carries a legacy ``cue_names`` entry.
        self.assertIsNotNone(widget._model)

    def test_property_cue_editor_update_terminals_is_noop(self) -> None:
        """Dialog close must not strip vfilter outputs via the preview-edit widget.

        Regression: :meth:`PreviewEditWidget._update_terminals` diffs the
        vfilter's current pyqtgraph outputs against :attr:`self.channels`
        (from :meth:`get_channel_list`) and removes every terminal not in that
        list. :class:`PropertyCueEditor.get_channel_list` returns ``[]`` by
        design -- its outputs come from the compiled property model, not a
        user-curated preview channel list -- so letting the base run strips
        all 52 outputs on dialog close and cascades pyqtgraph disconnects that
        blank every peer's ``channel_links``. The override makes
        ``_update_terminals`` a no-op for the property-cue editor so
        :meth:`FilterNode.update_node_after_settings_changed` is the sole
        authority for the terminal signature.
        """
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.widget import PropertyCueEditor
        editor = PropertyCueEditor(f=None)

        # Fake a filter_node with 52 outputs; the override must leave them untouched.
        filter_node = MagicMock()
        filter_node.outputs.return_value = {f"out_{i}": object() for i in range(52)}
        filter_node.removeTerminal = MagicMock()
        filter_node.addOutput = MagicMock()

        editor._update_terminals(filter_node)

        filter_node.removeTerminal.assert_not_called()
        filter_node.addOutput.assert_not_called()

    def test_migrate_name_list_skips_property_based_cue_filter(self) -> None:
        """No ``CueFilterModel`` for the property-based cue filter means skip migration.

        The old ``cue_names`` config key never existed on this vfilter, so if
        it ever shows up (e.g. hand-edited config) the migration helper must
        refuse to touch it instead of crashing on ``self._model.cues``.
        """
        from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

        f = MagicMock(spec=PropertyBasedCueFilter)
        f.filter_id = "Property Cues.0"
        f.property_model = MagicMock(cues=[])

        widget = self._build_widget()
        widget._filter = f
        widget._model = None  # as set by ``update_model`` for this flavour
        widget.configuration["cue_names"] = "Intro:0;Verse:1"

        widget._migrate_name_list()

        # Config left intact and model not fabricated -- migration is a
        # no-op for the property-based cue filter.
        self.assertEqual("Intro:0;Verse:1", widget.configuration["cue_names"])
        self.assertIsNone(widget._model)


if __name__ == "__main__":
    unittest.main()
