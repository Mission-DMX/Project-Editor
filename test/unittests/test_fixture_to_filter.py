"""Unit tests for :mod:`controller.show_manipulation.fixture_to_filter`.

Loads a representative set of OFL fixture definitions from the system-installed
``/var/cache/missionDMX/fixtures`` library and asserts that
:func:`place_fixture_filters_in_scene` wires up the expected adapter filters.
These tests guard against regressions like
`#330 <https://github.com/Mission-DMX/Project-Editor/issues/330>`__ where a channel
whose white segment is not literally named ``"White"`` silently fell back to the
RGB-only adapter, leaving the W segment unconnected.

The tests do not need a running fish instance; they build filters in-memory and
inspect the resulting ``channel_links`` / filter types.
"""
from __future__ import annotations

import json
import os
import unittest
from dataclasses import dataclass, field
from logging import getLogger
from typing import Iterable

# ``utility.resource_path`` resolves resources relative to the current working directory. Several
# modules imported below (notably ``model.ofl.color_name_dict``) load bundled data files at import
# time, so we must switch to the ``src`` directory before importing them. Store the original CWD so
# we can restore it later.
_ORIGINAL_CWD = os.getcwd()
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if os.path.isdir(_SRC_DIR):
    os.chdir(_SRC_DIR)

# A QApplication must exist before importing modules that build QPixmap / QGuiApplication state at
# import time. Create it eagerly here; keep the handle on the module to prevent garbage collection.
from PySide6.QtWidgets import QApplication  # noqa: E402

_APP = QApplication.instance() or QApplication([])

from controller.show_manipulation.fixture_to_filter import place_fixture_filters_in_scene  # noqa: E402
from model import BoardConfiguration, Scene  # noqa: E402
from model.filter import FilterTypeEnumeration  # noqa: E402
from model.ofl.fixture import UsedFixture  # noqa: E402
from model.ofl.ofl_fixture import OflFixture  # noqa: E402

logger = getLogger(__name__)

_FIXTURE_DIR = "/var/cache/missionDMX/fixtures"
"""System-installed OFL fixture library. Expected to be present on any host running the test suite."""


def _load_ofl(relative_path: str) -> OflFixture:
    """Load an OFL fixture definition from the system fixture library."""
    full_path = os.path.join(_FIXTURE_DIR, relative_path)
    with open(full_path, "r", encoding="UTF-8") as f:
        data = json.load(f)
    data["fileName"] = relative_path
    return OflFixture.model_validate(data)


def _mode_index(ofl: OflFixture, mode_name: str) -> int:
    for i, mode in enumerate(ofl.modes):
        if mode.name == mode_name:
            return i
    msg = f"Mode {mode_name!r} not found in {ofl.fileName}; available: {[m.name for m in ofl.modes]}"
    raise AssertionError(msg)


@dataclass
class FixtureBuildExpectation:
    """What we expect :func:`place_fixture_filters_in_scene` to produce for a given fixture mode."""

    fixture_path: str
    """Path relative to ``src/resources/fixtures``."""

    mode: str
    """Fixture mode name as defined in the OFL JSON."""

    expected_rgbw: int = 0
    """Number of ColorToRGBW adapters that should be instantiated."""

    expected_rgb: int = 0
    """Number of ColorToRGB adapters that should be instantiated."""

    expected_dimmer: int = 0
    """Number of DimmerGlobalBrightnessMixin vfilters that should be instantiated."""

    expected_16bit_split: int = 0
    """Number of 16-bit-to-dual-8-bit adapters (used for Pan/Tilt fine and double-channel dimmers)."""

    rgb_links_must_reference: list[str] = field(default_factory=list)
    """Channel names that must appear in the universe filter's channel_links mapping."""


class FixtureToFilterTest(unittest.TestCase):
    """Verify that fixture filter instantiation handles the common OFL channel layouts.

    Each sub-test exercises one fixture / mode combination. Add new cases to
    ``_CASES`` whenever a specific OFL layout starts regressing.
    """

    _CASES: list[FixtureBuildExpectation] = [
        # --- Simple adjacent RGB(W) fixtures: the happy path ---
        FixtureBuildExpectation(
            fixture_path="american-dj/saber-spot-rgbw.json",
            mode="RGBW",
            expected_rgbw=1,
            rgb_links_must_reference=["Red", "Green", "Blue", "White"],
        ),
        FixtureBuildExpectation(
            fixture_path="american-dj/saber-spot-rgbw.json",
            mode="RGBWD",
            expected_rgbw=1,
            expected_dimmer=1,
            rgb_links_must_reference=["Red", "Green", "Blue", "White", "Dimmer"],
        ),
        FixtureBuildExpectation(
            fixture_path="american-dj/saber-spot-rgbw.json",
            mode="RGBWD Strobe",
            expected_rgbw=1,
            expected_dimmer=1,
        ),
        FixtureBuildExpectation(
            fixture_path="stairville/sonicpulse-led-bar-10.json",
            mode="4Ch",
            expected_rgbw=1,
            rgb_links_must_reference=["Red", "Green", "Blue", "White"],
        ),
        FixtureBuildExpectation(
            fixture_path="stairville/sonicpulse-led-bar-10.json",
            mode="6Ch",
            expected_rgbw=1,
            expected_dimmer=1,
            rgb_links_must_reference=["Red", "Green", "Blue", "White", "Dimmer"],
        ),
        FixtureBuildExpectation(
            fixture_path="stairville/sonicpulse-led-bar-10.json",
            mode="11Ch",
            expected_rgbw=1,
            expected_dimmer=1,
        ),
        # --- Segment-based fixtures: the original #330 regression case ---
        # These are the exact fixtures that fell into the RGB-only branch because the
        # fourth colour channel was named "White Segment N" instead of literally "White".
        FixtureBuildExpectation(
            fixture_path="stairville/sonicpulse-led-bar-10.json",
            mode="23Ch",
            expected_rgbw=4,
            expected_dimmer=1,
            rgb_links_must_reference=[
                "Red Segment 1", "Green Segment 1", "Blue Segment 1", "White Segment 1",
                "Red Segment 4", "Green Segment 4", "Blue Segment 4", "White Segment 4",
            ],
        ),
        FixtureBuildExpectation(
            fixture_path="stairville/sonicpulse-led-bar-10.json",
            mode="39Ch",
            expected_rgbw=8,
            expected_dimmer=1,
            rgb_links_must_reference=["White Segment 1", "White Segment 8"],
        ),
        # --- Moving heads: Pan + Tilt (coarse-only) ---
        FixtureBuildExpectation(
            fixture_path="eurolite/led-tmh-9.json",
            mode="12-channel",
            expected_rgbw=1,
            expected_dimmer=1,
            # 'Pan fine' is at the end of this mode preceded by non-pan channels; no split expected.
            expected_16bit_split=0,
            rgb_links_must_reference=["Red", "Green", "Blue", "White"],
        ),
        # --- Moving head with full 16-bit Pan/Tilt (adjacent coarse + fine) ---
        FixtureBuildExpectation(
            fixture_path="varytec/hero-wash-340fx-rgbw-zoom.json",
            mode="16-channel",
            expected_rgbw=1,
            expected_dimmer=1,
            expected_16bit_split=2,  # Pan+Pan fine, Tilt+Tilt fine
        ),
        # --- Matrix-expanded fixture: 8-bit variant exposes adjacent RGBW per pixel ---
        FixtureBuildExpectation(
            fixture_path="showline/sl-nitro-510c.json",
            mode="RGBW 8-Bit 1-zone",
            expected_rgbw=1,
            # Master Dimmer + matrix "All Zones Intensity" both detected as dimmers.
            expected_dimmer=2,
        ),
        FixtureBuildExpectation(
            fixture_path="showline/sl-nitro-510c.json",
            mode="RGBW 8-Bit 2-zone",
            expected_rgbw=2,
            expected_dimmer=3,  # Master Dimmer + two zones' intensity
        ),
        # --- Non-RGBW fixtures should produce no colour adapter at all. HSI mode here still has
        #     an "Intensity" channel, which must still produce a dimmer vfilter. ---
        FixtureBuildExpectation(
            fixture_path="american-dj/saber-spot-rgbw.json",
            mode="HSI",
            expected_rgbw=0,
            expected_rgb=0,
            expected_dimmer=1,
        ),
        # --- RGB-only fixture: no White channel, must produce RGB adapter not RGBW ---
        FixtureBuildExpectation(
            fixture_path="generic/rgb-fader.json",
            mode="8 bit",
            expected_rgb=1,
            rgb_links_must_reference=["Red", "Green", "Blue"],
        ),
        FixtureBuildExpectation(
            fixture_path="generic/rgbw-fader.json",
            mode="8 bit",
            expected_rgbw=1,
            rgb_links_must_reference=["Red", "Green", "Blue", "White"],
        ),
        FixtureBuildExpectation(
            fixture_path="generic/drgbw-fader.json",
            mode="8 bit",
            expected_rgbw=1,
            expected_dimmer=1,
            rgb_links_must_reference=["Red", "Green", "Blue", "White", "Dimmer"],
        ),
    ]

    @classmethod
    def tearDownClass(cls) -> None:
        """Restore the working directory that was active before module import."""
        if _ORIGINAL_CWD and os.getcwd() != _ORIGINAL_CWD:
            os.chdir(_ORIGINAL_CWD)

    def _build_scene(self) -> tuple[BoardConfiguration, Scene]:
        board = BoardConfiguration()
        scene = Scene(0, "fixture_to_filter_test", board)
        board._add_scene(scene)
        return board, scene

    def _run_case(self, case: FixtureBuildExpectation) -> None:
        ofl = _load_ofl(case.fixture_path)
        mode_idx = _mode_index(ofl, case.mode)
        board, scene = self._build_scene()
        fixture = UsedFixture(board, ofl, mode_idx, parent_universe=1, start_index=0)

        filter_page = scene.pages[0]
        self.assertTrue(
            place_fixture_filters_in_scene(fixture, filter_page),
            f"place_fixture_filters_in_scene reported failure for {case.fixture_path} / {case.mode}",
        )

        counts = self._count_filter_types(scene.filters)
        self.assertEqual(
            counts.get(int(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGBW), 0),
            case.expected_rgbw,
            f"RGBW adapter count mismatch for {case.fixture_path} / {case.mode}: "
            f"got filters {self._summarise_filters(scene.filters)}",
        )
        self.assertEqual(
            counts.get(int(FilterTypeEnumeration.FILTER_ADAPTER_COLOR_TO_RGB), 0),
            case.expected_rgb,
            f"RGB adapter count mismatch for {case.fixture_path} / {case.mode}: "
            f"got filters {self._summarise_filters(scene.filters)}",
        )
        self.assertEqual(
            counts.get(int(FilterTypeEnumeration.VFILTER_DIMMER_BRIGHTNESS_MIXIN), 0),
            case.expected_dimmer,
            f"Dimmer vfilter count mismatch for {case.fixture_path} / {case.mode}: "
            f"got filters {self._summarise_filters(scene.filters)}",
        )
        self.assertEqual(
            counts.get(int(FilterTypeEnumeration.FILTER_ADAPTER_16BIT_TO_DUAL_8BIT), 0),
            case.expected_16bit_split,
            f"16-bit split filter count mismatch for {case.fixture_path} / {case.mode}: "
            f"got filters {self._summarise_filters(scene.filters)}",
        )

        universe_filter = self._universe_filter(scene.filters)
        self.assertIsNotNone(
            universe_filter,
            f"No universe output filter was created for {case.fixture_path} / {case.mode}",
        )
        for required_channel in case.rgb_links_must_reference:
            sanitised = required_channel.replace(" ", "_").replace("/", "_").replace("\\", "_")
            self.assertIn(
                sanitised,
                universe_filter.channel_links,
                f"Universe filter for {case.fixture_path} / {case.mode} is missing a link for "
                f"channel {required_channel!r}; got keys {list(universe_filter.channel_links.keys())!r}",
            )
            self.assertTrue(
                universe_filter.channel_links[sanitised],
                f"Universe filter link for {required_channel!r} in {case.fixture_path} / "
                f"{case.mode} is empty; the channel ended up unconnected.",
            )

    @staticmethod
    def _count_filter_types(filters: Iterable) -> dict[int, int]:
        """Return a mapping ``filter_type -> count``. Missing types default to zero on lookup."""
        counts: dict[int, int] = {}
        for f in filters:
            counts[int(f.filter_type)] = counts.get(int(f.filter_type), 0) + 1
        return counts

    @staticmethod
    def _summarise_filters(filters: Iterable) -> list[tuple[int, str]]:
        return [(f.filter_type, f.filter_id) for f in filters]

    @staticmethod
    def _universe_filter(filters: Iterable):
        for f in filters:
            if f.filter_type == FilterTypeEnumeration.FILTER_UNIVERSE_OUTPUT:
                return f
        return None

    def test_fixture_cases(self) -> None:
        """Validate every entry in ``_CASES`` as an independent sub-test."""
        for case in self._CASES:
            with self.subTest(fixture=case.fixture_path, mode=case.mode):
                self._run_case(case)

    def test_rgbw_white_segment_regression(self) -> None:
        """Explicit regression guard for #330.

        A segmented 23-channel fixture whose white channels are named
        ``"White Segment N"`` must produce one ColorToRGBW adapter per segment
        and must *not* fall back to the RGB-only adapter.
        """
        case = FixtureBuildExpectation(
            fixture_path="stairville/sonicpulse-led-bar-10.json",
            mode="23Ch",
            expected_rgbw=4,
            expected_rgb=0,
            expected_dimmer=1,
        )
        self._run_case(case)

        # Also verify the universe filter actually binds the white segments through the RGBW
        # adapter and does not leave them dangling.
        ofl = _load_ofl(case.fixture_path)
        mode_idx = _mode_index(ofl, case.mode)
        board, scene = self._build_scene()
        fixture = UsedFixture(board, ofl, mode_idx, parent_universe=1, start_index=0)
        place_fixture_filters_in_scene(fixture, scene.pages[0])
        universe_filter = self._universe_filter(scene.filters)
        self.assertIsNotNone(universe_filter)
        for segment in range(1, 5):
            key = f"White_Segment_{segment}"
            self.assertIn(key, universe_filter.channel_links)
            self.assertTrue(
                universe_filter.channel_links[key].endswith(":w"),
                f"Expected White Segment {segment} to be routed through the :w input of an RGBW "
                f"adapter but got link {universe_filter.channel_links[key]!r}",
            )


if __name__ == "__main__":
    unittest.main()
