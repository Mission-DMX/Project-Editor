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

    def test_passthrough_default(self) -> None:
        ctx = _ctx()
        out = build_postprocess_chain("unknown_capability", ctx)
        self.assertEqual((), out.filters)
        self.assertEqual(
            {"unknown_capability": ("cuef", "MH1__unknown_capability")},
            out.external_ports,
        )


class PanStrategyTest(unittest.TestCase):

    def _build(self, pan_range: tuple[int, int] | None = (0, 65535)) -> PostprocessOutput:
        return build_postprocess_chain("pan", _ctx(pan_range=pan_range))

    def test_pan_strategy_wires_chain(self) -> None:
        out = self._build()
        self.assertEqual(4, len(out.filters))
        by_type: dict[int, Filter] = {int(f.filter_type): f for f in out.filters}
        self.assertIn(int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN), by_type)
        self.assertIn(int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN), by_type)
        self.assertIn(int(FilterTypeEnumeration.FILTER_SWITCH_FLOAT), by_type)
        self.assertIn(int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE), by_type)

        sin_f = by_type[int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN)]
        cos_f = by_type[int(FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN)]
        switch_f = by_type[int(FilterTypeEnumeration.FILTER_SWITCH_FLOAT)]
        range_f = by_type[int(FilterTypeEnumeration.FILTER_ADAPTER_FLOAT_TO_16BIT_RANGE)]

        self.assertEqual("cuef:MH1__pan_value", sin_f.channel_links["value_in"])
        self.assertEqual("cuef:MH1__pan_value", cos_f.channel_links["value_in"])

        self.assertEqual("cuef:MH1__pan_curvesel", switch_f.channel_links["select"])
        self.assertEqual("cuef:MH1__pan_value", switch_f.channel_links["0"])
        self.assertEqual(f"{sin_f.filter_id}:value", switch_f.channel_links["1"])
        self.assertEqual(f"{cos_f.filter_id}:value", switch_f.channel_links["2"])

        self.assertEqual(f"{switch_f.filter_id}:out", range_f.channel_links["value_in"])

        self.assertEqual({"pan": (range_f.filter_id, "value")}, out.external_ports)

    def test_pan_range_defaults(self) -> None:
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

    def test_tilt_uses_tilt_range_and_channels(self) -> None:
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

    def setUp(self) -> None:
        self._previous = _factory._STRATEGIES.get("frost")

    def tearDown(self) -> None:
        if self._previous is None:
            _factory._STRATEGIES.pop("frost", None)
        else:
            _factory._STRATEGIES["frost"] = self._previous

    def test_register_overrides(self) -> None:
        marker_a = PostprocessOutput(filters=(), external_ports={"frost": ("A", "a")})
        marker_b = PostprocessOutput(filters=(), external_ports={"frost": ("B", "b")})

        register_strategy("frost", lambda _ctx: marker_a)
        self.assertIs(marker_a, build_postprocess_chain("frost", _ctx()))

        register_strategy("frost", lambda _ctx: marker_b)
        self.assertIs(marker_b, build_postprocess_chain("frost", _ctx()))


class StrobePassthroughTest(unittest.TestCase):

    def test_strobe_passthrough_warns(self) -> None:
        with self.assertLogs(_factory.__name__, level="WARNING") as cm:
            out = build_postprocess_chain("strobe", _ctx())
        self.assertTrue(any("strobe" in msg for msg in cm.output))
        self.assertEqual((), out.filters)
        self.assertEqual(
            {"strobe": ("cuef", "MH1__strobe")},
            out.external_ports,
        )


if __name__ == "__main__":
    unittest.main()
