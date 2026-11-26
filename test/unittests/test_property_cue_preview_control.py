"""Unit tests for the property-cue editor's :class:`PreviewController`.

Guards against the regression that broke leaving preview mode:
``stop()`` used to only interrupt the background thread, leaving
``vfilter.in_preview_mode = True`` and ``vfilter._channel_mapping``
populated from the preview build. The next ``transmit_to_fish`` after
the user pressed *Stop preview* therefore re-sent the preview filter
graph (with every ``__PREVIEW_CONST__…`` input of the postprocess chain)
instead of the production graph, and fish rejected the scene with a
type-mismatch on the cloned switch filter's ``select`` input.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None


_qapp = None


def _ensure_qapp():
    global _qapp
    if not _HAS_PYSIDE:
        return None
    from PySide6.QtWidgets import QApplication

    _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


def setUpModule() -> None:  # noqa: N802 — unittest hook
    """Ensure a QApplication exists before tests in this module run."""
    _ensure_qapp()


def _make_scene_and_vfilter():
    """Return a scene paired with a PropertyBasedCueFilter preconfigured for preview tests."""
    from model import BoardConfiguration, Scene
    from model.virtual_filters.property_cues.model import (
        EnabledCapability,
        FixtureSelection,
        FixtureSelectionEntry,
        ManualPropertyAssignment,
        PropertyAssignments,
        PropertyCue,
        PropertyStep,
        SelectionEntryKind,
    )
    from model.virtual_filters.property_cues.vfilter import PropertyBasedCueFilter

    show = BoardConfiguration()
    scene = Scene(0, "preview-control test", show)
    show._add_scene(scene)

    vfilter = PropertyBasedCueFilter(scene, "pcf")
    vfilter.property_model.fixture_selection = FixtureSelection(
        entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="MH1")],
        enabled_capabilities={EnabledCapability.POSITION},
    )
    vfilter.property_model.cues.append(PropertyCue(name="C1", steps=[
        PropertyStep(name="s0", duration_40hz=80, assignments={
            "fixture:MH1": PropertyAssignments(by_property={
                "position": ManualPropertyAssignment(values={
                    "pan_value": 0.5, "pan_curvesel": 0,
                    "tilt_value": 0.5, "tilt_curvesel": 0,
                }),
            }),
        }),
    ]))
    return scene, vfilter


@unittest.skipUnless(_HAS_PYSIDE, "Property cue editor requires PySide6")
class PreviewControllerStopTest(unittest.TestCase):
    """Verify PreviewController.stop resets preview flags on the vfilter."""

    def test_stop_resets_in_preview_mode(self) -> None:
        """Verify stopping preview resets in_preview_mode and clears the channel mapping."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import (
            PreviewController,
        )

        scene, vfilter = _make_scene_and_vfilter()
        controller = PreviewController(vfilter)

        # Simulate a round-trip through start by manually flipping the flags
        # the way start() would -- we don't want the real thread running in
        # a unit test. ``stop()`` must put both back to their pre-preview
        # values regardless of whether a thread is attached.
        vfilter.in_preview_mode = True
        vfilter._channel_mapping = {"MH1__pan": "stub:value"}

        controller.stop()

        self.assertFalse(
            vfilter.in_preview_mode,
            "Leaving preview must flip in_preview_mode back to False so "
            "the next transmit_to_fish ships the production graph.",
        )
        self.assertEqual(
            {}, vfilter._channel_mapping,
            "Leaving preview must clear the preview mapping so the production "
            "resolve_output_port_id path takes over.",
        )

    def test_stop_without_prior_start_is_safe(self) -> None:
        """Calling ``stop()`` on a controller that never started must no-op cleanly."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import (
            PreviewController,
        )

        scene, vfilter = _make_scene_and_vfilter()
        controller = PreviewController(vfilter)

        # The vfilter starts out of preview mode; stop() should leave that alone
        # (it still eagerly resets, which is also fine) and must not raise.
        vfilter.in_preview_mode = False
        vfilter._channel_mapping = {}

        controller.stop()
        self.assertFalse(vfilter.in_preview_mode)
        self.assertEqual({}, vfilter._channel_mapping)


if __name__ == "__main__":
    unittest.main()
