"""Unit tests for the property-based cue post-processing strategy table (WP8)."""

from __future__ import annotations

import unittest
from logging import getLogger

from model.filter import Filter, FilterTypeEnumeration
from model.virtual_filters.property_cues.postprocess import (
    CapabilityContext,
    PostprocessOutput,
    build_postprocess_chain,
    register_strategy,
)
from model.virtual_filters.property_cues.postprocess import factory as _factory

logger = getLogger(__name__)


class _SceneStub:
    """Minimal placeholder passed as ``scene`` to :class:`Filter`.

    :class:`Filter` only stores the reference; the postprocess factories never
    exercise any ``Scene`` method, so a bare sentinel is sufficient.
    """

    __slots__ = ()


def _ctx(**overrides: object) -> CapabilityContext:
    """Build a :class:`CapabilityContext` with sensible test defaults."""
    base: dict[str, object] = {
        "scene": _SceneStub(),
        "cue_filter_id": "cuef",
        "channel_name_prefix": "MH1",
    }
    base.update(overrides)
    return CapabilityContext(**base)  # type: ignore[arg-type]


class PassthroughDefaultTest(unittest.TestCase):
    """Verify the passthrough default behaviour for unknown capabilities."""

    def test_passthrough_default(self) -> None:
        """Verify an unknown capability yields a passthrough port and no filters."""
        ctx = _ctx()
        out = build_postprocess_chain("unknown_capability", ctx)
        self.assertEqual((), out.filters)
        self.assertEqual(
            {"unknown_capability": ("cuef", "MH1__unknown_capability")},
            out.external_ports,
        )


class PanStrategyTest(unittest.TestCase):
    """Verify the pan post-processing strategy builds the expected filter chain."""

    def _build(self, pan_range: tuple[int, int] | None = (0, 65535)) -> PostprocessOutput:
        """Return the pan post-process chain for the given pan range."""
        return build_postprocess_chain("pan", _ctx(pan_range=pan_range))

    def test_pan_strategy_wires_chain(self) -> None:
        """Verify the pan strategy wires sin/cos/rescale/switch/range filters correctly.

        L23: two additional ``FLOAT_TO_FLOAT_RANGE`` adapters remap the
        trig outputs from [-1, 1] to [0, 1] so the switch sees a consistent
        range across all three branches. The chain now has six filters
        (sin, cos, sin_to_01, cos_to_01, switch, range) instead of four.
        """
        out = self._build()
        self.assertEqual(6, len(out.filters))
        by_type: dict[int, list[Filter]] = {}
        for f in out.filters:
            by_type.setdefault(int(f.filter_type), []).append(f)
        self.assertEqual(1, len(by_type.get(int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN), [])))
        self.assertEqual(1, len(by_type.get(int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN), [])))
        self.assertEqual(1, len(by_type.get(int(FilterTypeEnumeration.FILTER_SWITCH_FLOAT), [])))
        self.assertEqual(1, len(by_type.get(int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE), [])))
        self.assertEqual(2, len(by_type.get(int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE), [])),
                         "L23: expected two [-1,1]->[0,1] trig rescalers")

        sin_f = by_type[int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN)][0]
        cos_f = by_type[int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN)][0]
        switch_f = by_type[int(FilterTypeEnumeration.FILTER_SWITCH_FLOAT)][0]
        range_f = by_type[int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE)][0]
        rescales = by_type[int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_FLOAT_RANGE)]

        self.assertEqual("cuef:MH1__pan_value", sin_f.channel_links["value_in"])
        self.assertEqual("cuef:MH1__pan_value", cos_f.channel_links["value_in"])

        # Both rescalers remap [-1, 1] -> [0, 1].
        for r in rescales:
            self.assertEqual("-1.0", r.filter_configurations["lower_bound_in"])
            self.assertEqual("1.0", r.filter_configurations["upper_bound_in"])
            self.assertEqual("0.0", r.filter_configurations["lower_bound_out"])
            self.assertEqual("1.0", r.filter_configurations["upper_bound_out"])
        sin_rescale = next(r for r in rescales if r.channel_links["value_in"] == f"{sin_f.filter_id}:value")
        cos_rescale = next(r for r in rescales if r.channel_links["value_in"] == f"{cos_f.filter_id}:value")

        self.assertEqual("cuef:MH1__pan_curvesel", switch_f.channel_links["select"])
        self.assertEqual("cuef:MH1__pan_value", switch_f.channel_links["0"])
        self.assertEqual(f"{sin_rescale.filter_id}:value", switch_f.channel_links["1"])
        self.assertEqual(f"{cos_rescale.filter_id}:value", switch_f.channel_links["2"])

        self.assertEqual(f"{switch_f.filter_id}:out", range_f.channel_links["value_in"])

        self.assertEqual({"pan": (range_f.filter_id, "value")}, out.external_ports)

    def test_pan_range_defaults(self) -> None:
        """Verify the pan strategy falls back to the full 16-bit range when no pan_range is given."""
        default_out = build_postprocess_chain("pan", _ctx(pan_range=None))
        range_filters = [
            f for f in default_out.filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE)
        ]
        self.assertEqual(1, len(range_filters))
        range_f = range_filters[0]
        self.assertEqual("0", range_f.filter_configurations["lower_bound_out"])
        self.assertEqual("65535", range_f.filter_configurations["upper_bound_out"])
        self.assertEqual("0.0", range_f.filter_configurations["lower_bound_in"])
        self.assertEqual("1.0", range_f.filter_configurations["upper_bound_in"])
        self.assertEqual("1", range_f.filter_configurations["limit_range"])


class TiltStrategyTest(unittest.TestCase):
    """Verify the tilt post-processing strategy uses the tilt range and channels."""

    def test_tilt_uses_tilt_range_and_channels(self) -> None:
        """Verify the tilt strategy references the tilt range and tilt_value/tilt_curvesel channels."""
        out = build_postprocess_chain("tilt", _ctx(tilt_range=(100, 50000)))
        range_f = next(
            f for f in out.filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE)
        )
        self.assertEqual("100", range_f.filter_configurations["lower_bound_out"])
        self.assertEqual("50000", range_f.filter_configurations["upper_bound_out"])
        switch_f = next(
            f for f in out.filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_SWITCH_FLOAT)
        )
        self.assertEqual("cuef:MH1__tilt_curvesel", switch_f.channel_links["select"])
        self.assertEqual("cuef:MH1__tilt_value", switch_f.channel_links["0"])
        self.assertEqual({"tilt": (range_f.filter_id, "value")}, out.external_ports)


class RegisterOverridesTest(unittest.TestCase):
    """Verify register_strategy overrides existing entries in the strategy table."""

    def setUp(self) -> None:
        """Snapshot the current frost strategy so it can be restored after each test."""
        self._previous = _factory._STRATEGIES.get("frost")

    def tearDown(self) -> None:
        """Restore the original frost strategy to isolate tests from one another."""
        if self._previous is None:
            _factory._STRATEGIES.pop("frost", None)
        else:
            _factory._STRATEGIES["frost"] = self._previous

    def test_register_overrides(self) -> None:
        """Verify re-registering a strategy replaces the previous entry."""
        marker_a = PostprocessOutput(filters=(), external_ports={"frost": ("A", "a")})
        marker_b = PostprocessOutput(filters=(), external_ports={"frost": ("B", "b")})

        register_strategy("frost", lambda _ctx: marker_a)
        self.assertIs(marker_a, build_postprocess_chain("frost", _ctx()))

        register_strategy("frost", lambda _ctx: marker_b)
        self.assertIs(marker_b, build_postprocess_chain("frost", _ctx()))


class DimmerStrategyTest(unittest.TestCase):
    """Verify the dimmer post-processing strategy wires the strobe generator chain."""

    def test_dimmer_strategy_wires_strobe_chain(self) -> None:
        """Verify the dimmer strategy wires strobefreq/duty_cycle adapters into the strobe generator."""
        out = build_postprocess_chain("dimmer", _ctx())
        self.assertEqual(3, len(out.filters))
        adapters = [f for f in out.filters
                    if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT)]
        self.assertEqual(2, len(adapters), "expect one float->8bit adapter each for strobefreq and duty_cycle")
        strobe_matches = [f for f in out.filters
                          if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)]
        self.assertEqual(1, len(strobe_matches))
        strobe_f = strobe_matches[0]

        freq_f = next(f for f in adapters if f.channel_links["value_in"].endswith("__strobefreq"))
        duty_f = next(f for f in adapters if f.channel_links["value_in"].endswith("__duty_cycle"))

        self.assertEqual("cuef:MH1__strobefreq", freq_f.channel_links["value_in"])
        self.assertEqual("cuef:MH1__duty_cycle", duty_f.channel_links["value_in"])

        # The strobe strategy reads from the raw channel ``brightness_raw`` (not
        # ``brightness``) so the serializer's channel_override_dict cannot
        # rewrite the strobe's own input to point at its own output.
        self.assertEqual("cuef:MH1__brightness_raw", strobe_f.channel_links["brightness"])
        self.assertEqual(f"{freq_f.filter_id}:value", strobe_f.channel_links["frequency"])
        self.assertEqual(f"{duty_f.filter_id}:value", strobe_f.channel_links["duty_cycle"])
        self.assertEqual("500.0", strobe_f.filter_configurations["slowest_period_ms"])

        self.assertEqual({"brightness": (strobe_f.filter_id, "value")}, out.external_ports)


if __name__ == "__main__":
    unittest.main()
