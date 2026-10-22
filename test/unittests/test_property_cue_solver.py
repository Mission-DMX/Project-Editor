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

    def test_mid_segment_edit_from_sibling(self) -> None:
        req_x_a = KeyframeRequest(timestep_40hz=0, requested_value=0.0, transition=TransferFunction.LINEAR)
        req_x_b = KeyframeRequest(timestep_40hz=100, requested_value=1.0, transition=TransferFunction.LINEAR)
        req_y_mid = KeyframeRequest(timestep_40hz=50, requested_value=0.5, transition=TransferFunction.LINEAR)
        group = RequestGroup(
            origin_label="prop_a",
            tree_depth=1,
            channel_names=frozenset({"X", "Y"}),
            requests={"X": [req_x_a, req_x_b], "Y": [req_y_mid]},
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X"), "Y": _spec("Y")},
            groups=[group],
        )
        solved = KeyframeSolver().solve(inp)
        x_frames = solved["X"].frames
        slots = [slot_from_seconds(f.timestamp) for f in x_frames]
        self.assertIn(50, slots)
        mid_frame = x_frames[slots.index(50)]
        self.assertAlmostEqual(0.5, _value(mid_frame), places=5)

    def test_specialisation_smaller_group_wins(self) -> None:
        contender_specific = RequestGroup(
            origin_label="specific",
            tree_depth=1,
            channel_names=frozenset({"X"}),
            requests={"X": [KeyframeRequest(timestep_40hz=10, requested_value=42.0)]},
        )
        contender_broad = RequestGroup(
            origin_label="broad",
            tree_depth=1,
            channel_names=frozenset({"X", "Y", "Z"}),
            requests={
                "X": [KeyframeRequest(timestep_40hz=10, requested_value=7.0)],
                "Y": [KeyframeRequest(timestep_40hz=10, requested_value=8.0)],
                "Z": [KeyframeRequest(timestep_40hz=10, requested_value=9.0)],
            },
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X"), "Y": _spec("Y"), "Z": _spec("Z")},
            groups=[contender_specific, contender_broad],
        )
        solved = KeyframeSolver().solve(inp)
        self.assertAlmostEqual(42.0, _value(solved["X"].frames[0]))
        self.assertAlmostEqual(9.0, _value(solved["Z"].frames[0]))
        self.assertAlmostEqual(8.0, _value(solved["Y"].frames[0]))

    def test_depth_tiebreak(self) -> None:
        shallow = RequestGroup(
            origin_label="shallow",
            tree_depth=1,
            channel_names=frozenset({"X", "Y"}),
            requests={"X": [KeyframeRequest(timestep_40hz=0, requested_value=1.0)]},
        )
        deep = RequestGroup(
            origin_label="deep",
            tree_depth=5,
            channel_names=frozenset({"X", "Y"}),
            requests={"X": [KeyframeRequest(timestep_40hz=0, requested_value=9.0)]},
        )
        inp = SolveInput(
            channel_specs={"X": _spec("X"), "Y": _spec("Y")},
            groups=[shallow, deep],
        )
        solved = KeyframeSolver().solve(inp)
        self.assertAlmostEqual(9.0, _value(solved["X"].frames[0]))

    def test_incompatible_transition_does_not_crash(self) -> None:
        group = RequestGroup(
            origin_label="mix",
            tree_depth=0,
            channel_names=frozenset({"X", "Y"}),
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
        x_frames = solved["X"].frames
        slots = [slot_from_seconds(f.timestamp) for f in x_frames]
        self.assertIn(40, slots)

    def test_sub_slot_collapse(self) -> None:
        group = RequestGroup(
            origin_label="dense",
            tree_depth=0,
            channel_names=frozenset({"X", "Y"}),
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

    def test_tie_group_index_fallback(self) -> None:
        first = RequestGroup(
            origin_label="first",
            tree_depth=2,
            channel_names=frozenset({"X"}),
            requests={"X": [KeyframeRequest(timestep_40hz=0, requested_value=11.0)]},
        )
        second = RequestGroup(
            origin_label="second",
            tree_depth=2,
            channel_names=frozenset({"X"}),
            requests={"X": [KeyframeRequest(timestep_40hz=0, requested_value=22.0)]},
        )
        inp = SolveInput(channel_specs={"X": _spec("X")}, groups=[first, second])
        solved = KeyframeSolver().solve(inp)
        self.assertAlmostEqual(11.0, _value(solved["X"].frames[0]))


class ChannelConsolidatorTest(unittest.TestCase):

    def test_identical_channels_collapse_to_alphabet_earliest(self) -> None:
        solver = KeyframeSolver()

        def _run(channel_name: str, value: float) -> list:
            group = RequestGroup(
                origin_label="g",
                tree_depth=0,
                channel_names=frozenset({channel_name}),
                requests={channel_name: [KeyframeRequest(timestep_40hz=0, requested_value=value)]},
            )
            inp = SolveInput(
                channel_specs={channel_name: _spec(channel_name)},
                groups=[group],
            )
            return solver.solve(inp)[channel_name].frames

        per_cue_frames = {
            "cue_1": {
                "beta": _run("beta", 7.0),
                "alpha": _run("alpha", 7.0),
                "gamma": _run("gamma", 42.0),
            },
        }
        specs = {
            "alpha": _spec("alpha"),
            "beta": _spec("beta"),
            "gamma": _spec("gamma"),
        }
        post = {"alpha": "pp", "beta": "pp", "gamma": "pp"}
        mapping = consolidate(per_cue_frames, specs, post)
        self.assertEqual("alpha", mapping.canonical("alpha"))
        self.assertEqual("alpha", mapping.canonical("beta"))
        self.assertEqual("gamma", mapping.canonical("gamma"))

    def test_different_postprocess_keeps_channels_separate(self) -> None:
        per_cue_frames = {
            "cue_1": {
                "alpha": [],
                "beta": [],
            },
        }
        specs = {"alpha": _spec("alpha"), "beta": _spec("beta")}
        post = {"alpha": "pp_a", "beta": "pp_b"}
        mapping = consolidate(per_cue_frames, specs, post)
        self.assertEqual("alpha", mapping.canonical("alpha"))
        self.assertEqual("beta", mapping.canonical("beta"))


if __name__ == "__main__":
    unittest.main()
