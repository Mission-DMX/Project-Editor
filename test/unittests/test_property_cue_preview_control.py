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

    def test_rewind_resets_cue_step_and_timecode(self) -> None:
        """Regression: rewind_to_start pauses and jumps back to cue 0 / t 0."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import (
            PreviewController,
        )
        _scene, vfilter = _make_scene_and_vfilter()
        controller = PreviewController(vfilter)
        # Fake a running state.
        controller.set_cue_index(3)
        controller.set_timecode(7.5)
        controller.set_playing(True)
        self.assertEqual(3, controller.cue_index)
        self.assertAlmostEqual(7.5, controller.timecode)
        self.assertTrue(controller.is_playing)

        controller.rewind_to_start()

        self.assertEqual(0, controller.cue_index)
        self.assertAlmostEqual(0.0, controller.timecode)
        self.assertFalse(controller.is_playing)

    def test_toggle_playing_flips_state(self) -> None:
        """Regression: toggle_playing flips the playing flag and returns the new state."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import (
            PreviewController,
        )
        _scene, vfilter = _make_scene_and_vfilter()
        controller = PreviewController(vfilter)
        self.assertFalse(controller.is_playing)
        self.assertTrue(controller.toggle_playing())
        self.assertTrue(controller.is_playing)
        self.assertFalse(controller.toggle_playing())
        self.assertFalse(controller.is_playing)

    def test_format_seven_seg_matches_cue_editor(self) -> None:
        """Regression: 7-seg format matches the existing cue editor's 12-char layout."""
        from view.show_mode.editor.node_editor_widgets.property_cue_editor.preview_control import (
            _format_seven_seg,
        )
        # Cue 0, timecode 0 -> "0" + 10-digit zero-padded time + leading-space padding to 12.
        self.assertEqual(12, len(_format_seven_seg(0, 0.0)))
        self.assertTrue(_format_seven_seg(0, 0.0).strip().startswith("0"))
        # Cue 42 should prefix as "42".
        formatted = _format_seven_seg(42, 1.5)
        self.assertEqual(12, len(formatted))
        self.assertTrue(formatted.strip().startswith("42"))

    def test_push_seven_seg_dedups_identical_content(self) -> None:
        """Regression: unchanged 7-seg content must not re-send a desk_update to fish.

        The 100 ms preview tick fires regardless of playback state; when
        paused and nothing is navigating, consecutive ticks produce the
        same cue/timecode string. Routing every one of those through
        ``set_seven_seg_display_content`` -- which unconditionally emits a
        ``desk_update`` protobuf containing ``selected_bank = 0`` -- had fish
        logging "Failed to change active bank" ten times a second and
        backed the ArtNet writer up to the point of dropping output packets.
        """
        from unittest.mock import patch
        from view.show_mode.editor.node_editor_widgets.property_cue_editor import (
            preview_control as pc,
        )
        _scene, vfilter = _make_scene_and_vfilter()
        controller = pc.PreviewController(vfilter)
        controller.set_cue_index(0)
        controller.set_timecode(1.5)

        with patch.object(pc, "set_seven_seg_display_content") as mock_send:
            controller._push_seven_seg()
            controller._push_seven_seg()
            controller._push_seven_seg()

        self.assertEqual(1, mock_send.call_count,
                         "Identical consecutive 7-seg pushes must dedup to a single call")

        # A content change still gets through.
        with patch.object(pc, "set_seven_seg_display_content") as mock_send:
            controller._push_seven_seg()  # unchanged
            controller.set_timecode(2.0)   # pushes once from set_timecode
            controller._push_seven_seg()  # dedups again
        # ``set_timecode`` with no running thread does not push, so only the
        # explicit push after the change should hit the mock; verify that
        # the dedup lets through exactly one call.
        self.assertEqual(1, mock_send.call_count,
                         "Timecode change must emit exactly one desk update")

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
