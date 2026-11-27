"""Unit tests for the keyframe solver and channel consolidator (WP3)."""

import unittest
from logging import getLogger

from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.channel_consolidator import consolidate
from model.virtual_filters.property_cues.channel_spec import ChannelSpec
from model.virtual_filters.property_cues.keyframe_request import KeyframeRequest
from model.virtual_filters.property_cues.solver import (
    KeyframeSolver,
    RequestGroup,
    SolveInput,
    SolvedChannel,
)
from model.virtual_filters.property_cues.solver_helpers import slot_from_seconds

logger = getLogger(__name__)


def _spec(name: str, dt: DataType = DataType.DT_DOUBLE) -> ChannelSpec:
    return ChannelSpec(name=name, data_type=dt)


def _value(frame) -> float:
    return float(frame._states[0]._value)


class KeyframeSolverTest(unittest.TestCase):
    """Tests for the KeyframeSolver conflict resolution and interpolation."""

    def test_solver_emits_one_frame_per_request(self) -> None:
        """Verify the solver emits exactly one frame per surviving request.

        Before L4 the solver injected synthetic mid-frames on channel X at
        slots where a sibling channel Y had a keyframe. That mid-frame
        insertion has moved into :func:`_native_builder._state_for`: the
        solver now returns the requested frames unmodified and the native
        builder interpolates when another channel contributes a slot this
        one does not touch (see
        :class:`test_property_cue_end_to_end.PropertyCueEndToEndTests.test_unrelated_keyframe_does_not_reshape_fade`).
        """
        req_x_a = KeyframeRequest(timestep_40hz=0, requested_value=0.0, transition=TransferFunction.LINEAR)
        req_x_b = KeyframeRequest(timestep_40hz=100, requested_value=1.0, transition=TransferFunction.LINEAR)
        req_y_mid = KeyframeRequest(timestep_40hz=50, requested_value=0.5, transition=TransferFunction.LINEAR)
        group = RequestGroup(
            origin_label="prop_a",


            requests={"X": [req_x_a, req_x_b], "Y": [req_y_mid]},
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X"), "Y": _spec("Y")},
            groups=[group],
        )
        solved = KeyframeSolver().solve(inp)
        x_slots = [slot_from_seconds(f.timestamp) for f in solved["X"].frames]
        self.assertEqual([0, 100], sorted(x_slots))
        y_slots = [slot_from_seconds(f.timestamp) for f in solved["Y"].frames]
        self.assertEqual([50], y_slots)

    def test_last_emission_wins_at_contested_slot(self) -> None:
        """Verify last-emitted group wins when two groups share a channel/slot.

        Before L6, the solver ranked groups by (channel_count, tree_depth) and
        the "more specialised" group won. That tiebreak has moved into
        :func:`_collect_cue`, which now emits only the winning assignment per
        (fixture, property, step). The solver itself does last-write-wins
        deduplication: a group emitted later in the per-cue stream (higher
        group index) overrides any earlier group's request on the same slot.
        """
        earlier = RequestGroup(
            origin_label="earlier",


            requests={"X": [KeyframeRequest(timestep_40hz=10, requested_value=7.0)]},
        )
        later = RequestGroup(
            origin_label="later",


            requests={"X": [KeyframeRequest(timestep_40hz=10, requested_value=42.0)]},
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X")}, groups=[earlier, later],
        )
        solved = KeyframeSolver().solve(inp)
        self.assertAlmostEqual(42.0, _value(solved["X"].frames[0]))

    def test_incompatible_transition_does_not_crash(self) -> None:
        """Verify the solver tolerates mixed transition kinds within the same channel.

        Updated for L4: cross-channel insertion moved to the native builder, so
        the solver no longer tries to interpolate across the mixed-transition
        pair. It emits the two X frames at the original slots and the Y frame
        at its own slot; the native builder handles any cross-channel fills.
        """
        group = RequestGroup(
            origin_label="mix",


            requests={
                "X": [
                    KeyframeRequest(timestep_40hz=0, requested_value=0.0, transition=TransferFunction.EDGE),
                    KeyframeRequest(timestep_40hz=80, requested_value=1.0, transition=TransferFunction.SIGMOIDAL),
                ],
                "Y": [KeyframeRequest(timestep_40hz=40, requested_value=0.5)],
            },
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X"), "Y": _spec("Y")},
            groups=[group],
        )
        solved = KeyframeSolver().solve(inp)
        x_slots = [slot_from_seconds(f.timestamp) for f in solved["X"].frames]
        self.assertEqual([0, 80], sorted(x_slots))
        y_slots = [slot_from_seconds(f.timestamp) for f in solved["Y"].frames]
        self.assertEqual([40], y_slots)

    def test_sub_slot_collapse(self) -> None:
        """Verify requests sharing a timestep collapse to a single frame per channel."""
        group = RequestGroup(
            origin_label="dense",


            requests={
                "X": [
                    KeyframeRequest(timestep_40hz=0, requested_value=0.0, transition=TransferFunction.LINEAR),
                    KeyframeRequest(timestep_40hz=10, requested_value=1.0, transition=TransferFunction.LINEAR),
                ],
                "Y": [
                    KeyframeRequest(timestep_40hz=5, requested_value=0.1),
                    KeyframeRequest(timestep_40hz=5, requested_value=0.9),
                ],
            },
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X"), "Y": _spec("Y")},
            groups=[group],
        )
        solved = KeyframeSolver().solve(inp)
        y_slots = [slot_from_seconds(f.timestamp) for f in solved["Y"].frames]
        self.assertEqual(1, y_slots.count(5))
        x_slots = [slot_from_seconds(f.timestamp) for f in solved["X"].frames]
        for slot in x_slots:
            self.assertEqual(1, x_slots.count(slot))

    def test_last_write_wins_on_identical_slot(self) -> None:
        """Verify later group index wins on a tied slot (last-write-wins).

        After L6, precedence is resolved in :func:`_collect_cue` so the
        solver receives at most one group per (fixture, property) per step.
        For any residual slot-level collision, the solver keeps the later
        emission — matching "last write wins" semantics in authoring order.
        """
        first = RequestGroup(
            origin_label="first",


            requests={"X": [KeyframeRequest(timestep_40hz=0, requested_value=11.0)]},
        )
        second = RequestGroup(
            origin_label="second",


            requests={"X": [KeyframeRequest(timestep_40hz=0, requested_value=22.0)]},
        )
        inp = SolveInput(channel_specs={"X": _spec("X")}, groups=[first, second])
        solved = KeyframeSolver().solve(inp)
        self.assertAlmostEqual(22.0, _value(solved["X"].frames[0]))


class ChannelConsolidatorTest(unittest.TestCase):
    """Tests for the channel consolidator that collapses identical frame streams."""

    def test_identical_channels_collapse_to_alphabet_earliest(self) -> None:
        """Same local name on different prefixes consolidates on identical streams.

        The consolidator only collapses channels that share the same local
        port name (the segment after ``__``) so that semantically distinct
        ports on one fixture -- e.g. ``brightness_raw`` vs ``strobefreq`` --
        can never merge even when their frame streams happen to match.
        Here both ``MH1__brightness`` and ``MH2__brightness`` carry the
        same value (7.0) at the same slot, so they collapse onto the
        alphabetically-earliest ``MH1__brightness``.
        """
        solver = KeyframeSolver()

        def _run(channel_name: str, value: float) -> list:
            group = RequestGroup(
                origin_label="g",
                requests={channel_name: [KeyframeRequest(timestep_40hz=0, requested_value=value)]},
            )
            inp = SolveInput(
                channel_specs={channel_name: _spec(channel_name)},
                groups=[group],
            )
            return solver.solve(inp)[channel_name].frames

        per_cue_frames = {
            "cue_1": {
                "MH2__brightness": _run("MH2__brightness", 7.0),
                "MH1__brightness": _run("MH1__brightness", 7.0),
                "MH1__pan": _run("MH1__pan", 42.0),
            },
        }
        specs = {
            "MH1__brightness": _spec("MH1__brightness"),
            "MH2__brightness": _spec("MH2__brightness"),
            "MH1__pan": _spec("MH1__pan"),
        }
        post = {"MH1__brightness": "pp", "MH2__brightness": "pp", "MH1__pan": "pp"}
        mapping = consolidate(per_cue_frames, specs)
        self.assertEqual("MH1__brightness", mapping.canonical("MH1__brightness"))
        self.assertEqual("MH1__brightness", mapping.canonical("MH2__brightness"))
        self.assertEqual("MH1__pan", mapping.canonical("MH1__pan"))

    def test_same_prefix_different_locals_never_merge(self) -> None:
        """Two DT_DOUBLE channels on the same fixture must stay separate.

        Regression for the dimmer configure failure observed on fish:
        ``brightness_raw``, ``strobefreq`` and ``duty_cycle`` are all
        DT_DOUBLE and carry empty frame streams when the user has not
        dialed any dimmer assignments, but they MUST remain declared as
        three distinct output channels on the native cue filter because
        the strobe post-processing chain references each by its specific
        local name.
        """
        per_cue_frames = {
            "cue_1": {
                "MH1__brightness_raw": [],
                "MH1__strobefreq": [],
                "MH1__duty_cycle": [],
            },
        }
        specs = {
            "MH1__brightness_raw": _spec("MH1__brightness_raw"),
            "MH1__strobefreq": _spec("MH1__strobefreq"),
            "MH1__duty_cycle": _spec("MH1__duty_cycle"),
        }
        post = {
            "MH1__brightness_raw": "dimmer:None:None",
            "MH1__strobefreq": "dimmer:None:None",
            "MH1__duty_cycle": "dimmer:None:None",
        }
        mapping = consolidate(per_cue_frames, specs)
        self.assertEqual("MH1__brightness_raw", mapping.canonical("MH1__brightness_raw"))
        self.assertEqual("MH1__strobefreq", mapping.canonical("MH1__strobefreq"))
        self.assertEqual("MH1__duty_cycle", mapping.canonical("MH1__duty_cycle"))

    def test_divergent_postprocess_wiring_resolved_at_chain_cache(self) -> None:
        """Verify channels with identical frame streams still consolidate.

        Phase 4 removed the ``postprocess_signatures`` arg from
        :func:`consolidate`. Differing post-process wiring (e.g. two
        fixtures whose strobe-freq streams diverge even though brightness
        consolidates) is now resolved at the chain-cache key level in
        :func:`_build_ports` (L1), not here. This test documents the new
        boundary: identical per-channel frame streams collapse unconditionally.
        """
        per_cue_frames = {
            "cue_1": {
                "MH1__brightness": [],
                "MH2__brightness": [],
            },
        }
        specs = {"MH1__brightness": _spec("MH1__brightness"), "MH2__brightness": _spec("MH2__brightness")}
        mapping = consolidate(per_cue_frames, specs)
        self.assertEqual("MH1__brightness", mapping.canonical("MH1__brightness"))
        self.assertEqual("MH1__brightness", mapping.canonical("MH2__brightness"))


if __name__ == "__main__":
    unittest.main()
