"""Save → reload roundtrip test for the Dimmer Director filter (type 84).

Builds a maximally-featured randomised model, saves it to a show file under ``/tmp`` using
the standard editor save path, reloads it from the same file, and asserts every piece of
model and I/O state matches the original.

See ``test_dimmer_director_fish.py`` for the companion fish-instantiation test — it is
intentionally kept in a separate module because ``execute_board_configuration`` constructs
its own ``QApplication`` and would collide with the one this module needs at import time
(``controller.file.read`` has module-level ``QIcon`` constructors that require a
``QGuiApplication`` to exist).
"""
from __future__ import annotations

import os
import random
import tempfile
import unittest

from PySide6.QtWidgets import QApplication

# A QApplication must exist before any ``view``-side module (reachable from
# ``controller.file.read``) is imported because some of those modules construct QIcons /
# QPixmaps at module import time.
if QApplication.instance() is None:
    _qapp = QApplication([])

from controller.file.read import read_document  # noqa: E402
from controller.file.write import write_document  # noqa: E402
from model import BoardConfiguration, Scene  # noqa: E402
from model.filter import DataType, FilterTypeEnumeration  # noqa: E402
from model.filter_data.cues.cue import Cue, KeyFrame, StateDouble  # noqa: E402
from model.filters.dimmer_director import (  # noqa: E402
    DimmerCurve,
    DimmerCurveType,
    DimmerDirectorFilter,
    DimmerGroup,
    EffectCurve,
    EffectCurveMode,
)

_SEED = 0xDD84


def _random_name(rng: random.Random, prefix: str) -> str:
    """Generate a sanitize-safe random channel name (ASCII letters/digits only)."""
    suffix = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
    return f"{prefix}_{suffix}"


def _random_cue(rng: random.Random) -> Cue:
    """Generate a Cue with 2-6 keyframes of random timestamps and values."""
    cue = Cue()
    cue.add_channel("value", DataType.DT_DOUBLE)
    kf_count = rng.randint(2, 6)
    timestamps = sorted(rng.uniform(0.05, 3.0) for _ in range(kf_count))
    transitions = ("edg", "lin", "sig", "e_i", "e_o")
    for ts in timestamps:
        kf = KeyFrame(cue)
        kf.timestamp = ts
        state = StateDouble(rng.choice(transitions))
        state._value = round(rng.uniform(-1.0, 1.0), 4)
        kf.append_state(state)
        cue.insert_frame(kf)
    return cue


def _build_random_dimmer_director(scene: Scene, rng: random.Random, filter_id: str) -> DimmerDirectorFilter:
    """Populate a dimmer director using all features so a roundtrip exercises every path."""
    f = DimmerDirectorFilter(
        scene=scene,
        filter_id=filter_id,
        filter_type=FilterTypeEnumeration.FILTER_DIMMER_DIRECTOR,
        pos=(float(rng.randint(-200, 200)), float(rng.randint(-200, 200))),
    )
    f.global_mixin_count = rng.randint(1, 3)
    f.global_offset_count = rng.randint(0, 2)
    group_count = rng.randint(2, 4)
    used_names: set[str] = set()
    for _ in range(group_count):
        while True:
            name = _random_name(rng, "grp")
            if name not in used_names:
                used_names.add(name)
                break
        group = f.add_group(name)
        if group is None:
            continue
        group.x = rng.randint(1, 4)
        group.y = rng.randint(1, 3)
        group.z = rng.randint(1, 2)
        group.n_mix_group = rng.randint(0, 2)
        group.n_off_group = rng.randint(0, 2)
        group.phase_x = rng.randint(-4, 4)
        group.phase_y = rng.randint(-4, 4)
        group.phase_z = rng.randint(-4, 4)
        if not f.update_group(len(f.groups) - 1, group):
            raise RuntimeError(f"update_group rejected the random group {group.name!r}")

    effect_count = rng.randint(2, 4)
    for i in range(effect_count):
        curve = f.add_effect_curve(f"eff_{i}")
        curve.mode = rng.choice(list(EffectCurveMode))
        curve.threshold = round(rng.uniform(0.0, 1.0), 4)
        curve.window = rng.randint(1, 8)
        if i % 2 == 0:
            # Even curves get keyframes — their samples cache is derived from the cue.
            curve.cue = _random_cue(rng)
            # Pre-populate samples so the serialize path writes a non-empty cache even
            # before the editor would trigger a resample.
            curve.samples = [round(rng.uniform(-1.0, 1.0), 4) for _ in range(rng.randint(6, 16))]
        else:
            # Odd curves simulate CSV-imported data (no keyframes, raw sample list).
            curve.cue = None
            curve.samples = [round(rng.uniform(-1.0, 1.0), 4) for _ in range(rng.randint(6, 16))]

    dimmer_count = rng.randint(2, 4)
    for i in range(dimmer_count):
        curve = f.add_dimmer_curve(f"dim_{i}")
        curve.type = rng.choice(list(DimmerCurveType))
        if curve.type == DimmerCurveType.BEZIER:
            curve.params = [round(rng.uniform(0.0, 1.0), 4) for _ in range(4)]

    recall_count = rng.randint(1, 3)
    for _ in range(recall_count):
        f.add_recall()
    for recall_idx in range(len(f.recalls)):
        for group_idx in range(len(f.groups)):
            eff = rng.randrange(len(f.effect_curves))
            dim = rng.randrange(len(f.dimmer_curves))
            f.set_recall_selection(recall_idx, group_idx, eff, dim)

    return f


def _snapshot(f: DimmerDirectorFilter) -> dict:
    """Capture every piece of filter state for later equality comparison."""
    def group_snapshot(g: DimmerGroup) -> dict:
        return {
            "name": g.name,
            "x": g.x, "y": g.y, "z": g.z,
            "n_mix_group": g.n_mix_group, "n_off_group": g.n_off_group,
            "phase_x": g.phase_x, "phase_y": g.phase_y, "phase_z": g.phase_z,
        }

    def effect_snapshot(c: EffectCurve) -> dict:
        kf_dump = None
        if c.cue is not None:
            kf_dump = [
                (round(kf.timestamp, 6), kf._states[0]._transition_type, round(float(kf._states[0]._value), 6))
                for kf in c.cue._frames
            ]
        return {
            "name": c.name,
            "mode": c.mode,
            "threshold": round(c.threshold, 6),
            "window": c.window,
            "samples": [round(s, 6) for s in c.samples],
            "keyframes": kf_dump,
        }

    def dimmer_snapshot(c: DimmerCurve) -> dict:
        return {
            "name": c.name,
            "type": c.type,
            "params": [round(p, 6) for p in c.params],
        }

    return {
        "filter_id": f.filter_id,
        "filter_type": int(f.filter_type),
        "global_mixin_count": f.global_mixin_count,
        "global_offset_count": f.global_offset_count,
        "groups": [group_snapshot(g) for g in f.groups],
        "effect_curves": [effect_snapshot(c) for c in f.effect_curves],
        "dimmer_curves": [dimmer_snapshot(c) for c in f.dimmer_curves],
        "recalls": [list(r.selections) for r in f.recalls],
        "in_data_types": dict(f.in_data_types),
        "out_data_types": dict(f.out_data_types),
    }


class DimmerDirectorRoundtripTest(unittest.TestCase):
    """Save a randomised dimmer director to a show file in /tmp and reload it."""

    def test_show_file_roundtrip_preserves_all_state(self) -> None:
        """Every field of a maximally-featured filter must survive write → read unchanged."""
        rng = random.Random(_SEED)

        show = BoardConfiguration(show_name="dimmer director roundtrip test")
        scene = Scene(0, "Dimmer Director Scene", show)
        show._add_scene(scene)
        original = _build_random_dimmer_director(scene, rng, filter_id="dd_roundtrip")
        scene.append_filter(original)

        snapshot_before = _snapshot(original)
        self.assertGreater(len(snapshot_before["in_data_types"]), 0)
        self.assertGreater(len(snapshot_before["out_data_types"]), 0)
        self.assertGreater(len(snapshot_before["effect_curves"]), 0)
        self.assertGreater(len(snapshot_before["dimmer_curves"]), 0)
        self.assertGreater(len(snapshot_before["recalls"]), 0)

        fd, show_path = tempfile.mkstemp(
            prefix="dimmer_director_roundtrip_",
            suffix=".show",
            dir="/tmp",
        )
        os.close(fd)
        try:
            self.assertTrue(write_document(show_path, show), f"write_document failed for {show_path}")
            self.assertTrue(os.path.getsize(show_path) > 0, "show file should not be empty")

            reloaded_show = BoardConfiguration()
            self.assertTrue(read_document(show_path, reloaded_show), "read_document failed")

            self.assertEqual(len(reloaded_show.scenes), 1, "expected exactly one scene")
            reloaded_scene = reloaded_show.scenes[0]
            matches = [f for f in reloaded_scene.filters if f.filter_id == "dd_roundtrip"]
            self.assertEqual(len(matches), 1, "the dimmer director filter was not reloaded")
            reloaded = matches[0]
            self.assertIsInstance(reloaded, DimmerDirectorFilter)

            self.maxDiff = None
            snapshot_after = _snapshot(reloaded)
            self.assertEqual(snapshot_before, snapshot_after, "roundtrip altered state")
        finally:
            if os.path.exists(show_path):
                os.remove(show_path)
            backup = os.path.splitext(show_path)[0] + ".show_backup"
            if os.path.exists(backup):
                os.remove(backup)


if __name__ == "__main__":
    unittest.main()
