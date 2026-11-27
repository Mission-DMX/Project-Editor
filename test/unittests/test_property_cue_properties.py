"""Unit tests for property-based cue properties and distribution (WP4)."""

from __future__ import annotations

import math
import unittest
from logging import getLogger

from model.color_hsi import ColorHSI
from model.filter import DataType
from model.filter_data.transfer_function import TransferFunction
from model.virtual_filters.property_cues.distribution import Distribution, DistributionMethod
from model.virtual_filters.property_cues.properties import (
    CURVE_SIN,
    BeamProperty,
    ColorProperty,
    DimmerProperty,
    FrostProperty,
    GoboProperty,
    PositionProperty,
    distribute_colors,
    seconds_to_timesteps,
)

logger = getLogger(__name__)


_CONSTANT = Distribution(method=DistributionMethod.CONSTANT)


class DistributionTest(unittest.TestCase):
    """Tests for the Distribution delay calculation across methods."""

    def test_constant_zero_delay(self) -> None:
        """Verify CONSTANT method yields a zero delay regardless of parameters."""
        dist = Distribution(method=DistributionMethod.CONSTANT, phase_offset=99.0, amplitude=12.0)
        for idx in range(5):
            self.assertEqual(0.0, dist.delay_for_child(idx))

    def test_phase_linear_sequence(self) -> None:
        """Verify PHASE_LINEAR produces evenly spaced delays scaled by amplitude."""
        dist = Distribution(method=DistributionMethod.PHASE_LINEAR, phase_offset=0.5, amplitude=1.0)
        delays = [dist.delay_for_child(i) for i in range(4)]
        self.assertEqual([0.0, 0.5, 1.0, 1.5], delays)

    def test_phase_sin_amplitude(self) -> None:
        """Verify PHASE_SIN delays remap to [0, amplitude] preserving sine shape (L7).

        The previous implementation returned ``amplitude * sin(phase * i)``
        which produced negative delays for half of the sine wave; those
        pushed keyframes into negative time and got dropped by the solver.
        The current implementation returns ``amplitude * (sin(phase * i) + 1) / 2``
        so the delay sweeps [0, amplitude] and the shape of the wave
        (relative delays across children) is preserved.
        """
        dist = Distribution(method=DistributionMethod.PHASE_SIN, phase_offset=math.pi / 2, amplitude=2.0)
        delays = [dist.delay_for_child(i) for i in range(4)]
        self.assertAlmostEqual(1.0, delays[0], places=6)
        self.assertAlmostEqual(2.0, delays[1], places=6)
        self.assertAlmostEqual(1.0, delays[2], places=6)
        self.assertAlmostEqual(0.0, delays[3], places=6)
        # All delays non-negative.
        for d in delays:
            self.assertGreaterEqual(d, 0.0)

    def test_phase_cos_amplitude(self) -> None:
        """Verify PHASE_COS delays remap to [0, amplitude] preserving cosine shape (L7)."""
        dist = Distribution(method=DistributionMethod.PHASE_COS, phase_offset=math.pi, amplitude=1.0)
        delays = [dist.delay_for_child(i) for i in range(3)]
        self.assertAlmostEqual(1.0, delays[0], places=6)
        self.assertAlmostEqual(0.0, delays[1], places=6)
        self.assertAlmostEqual(1.0, delays[2], places=6)

    def test_phase_saw_shape(self) -> None:
        """Verify PHASE_SAW produces a non-negative sawtooth from 0 to amplitude (L7)."""
        dist = Distribution(method=DistributionMethod.PHASE_SAW, phase_offset=math.pi, amplitude=1.0)
        # phase_offset=pi -> fraction increments by 0.5 per step.
        # child 0 -> fraction 0.0 -> delay 0.0
        # child 1 -> fraction 0.5 -> delay 0.5
        # child 2 -> fraction 0.0 -> delay 0.0 (wraps)
        delays = [dist.delay_for_child(i) for i in range(3)]
        self.assertAlmostEqual(0.0, delays[0], places=6)
        self.assertAlmostEqual(0.5, delays[1], places=6)
        self.assertAlmostEqual(0.0, delays[2], places=6)


class DimmerPropertyTest(unittest.TestCase):
    """Tests for DimmerProperty channel specs and request generation."""

    def test_channel_specs(self) -> None:
        """Verify raw brightness channel is named brightness_raw to avoid strobe collision.

        The raw brightness channel is named ``brightness_raw`` so it cannot
        collide with the ``brightness`` port the strobe post-processing strategy
        publishes (see the self-link bug fixed in ``_dimmer_strategy``).
        """
        specs = DimmerProperty().channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "brightness_raw": DataType.DT_DOUBLE,
                "strobefreq": DataType.DT_DOUBLE,
                "duty_cycle": DataType.DT_DOUBLE,
            },
            names_to_types,
        )

    def test_single_request_at_step_start(self) -> None:
        """Verify one request per channel is emitted at the step start timestep."""
        prop = DimmerProperty(
            brightness=0.75, strobefreq=0.0, duty_cycle=200.0, transition=TransferFunction.LINEAR,
        )
        reqs = prop.generate_requests(step_start_40hz=100, step_duration_40hz=400, child_index=0, distribution=_CONSTANT)
        self.assertIn("brightness_raw", reqs)
        self.assertEqual(1, len(reqs["brightness_raw"]))
        req = reqs["brightness_raw"][0]
        self.assertEqual(100, req.timestep_40hz)
        self.assertEqual(0.75, req.requested_value)
        self.assertIs(TransferFunction.LINEAR, req.transition)
        strobe_req = reqs["strobefreq"][0]
        self.assertEqual(100, strobe_req.timestep_40hz)
        self.assertEqual(0.0, strobe_req.requested_value)
        duty_req = reqs["duty_cycle"][0]
        self.assertEqual(100, duty_req.timestep_40hz)
        self.assertEqual(200.0, duty_req.requested_value)
        self.assertIs(TransferFunction.LINEAR, duty_req.transition)

    def test_default_duty_cycle_is_balanced(self) -> None:
        """Verify the default duty cycle emits the balanced midpoint value (128)."""
        reqs = DimmerProperty().generate_requests(
            step_start_40hz=0, step_duration_40hz=40, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(128.0, reqs["duty_cycle"][0].requested_value)

    def test_phase_linear_delays_children(self) -> None:
        """Verify PHASE_LINEAR distribution offsets each child's request timestep."""
        prop = DimmerProperty(brightness=1.0)
        dist = Distribution(method=DistributionMethod.PHASE_LINEAR, phase_offset=0.5, amplitude=1.0)
        starts: list[int] = []
        for child in range(4):
            reqs = prop.generate_requests(
                step_start_40hz=0, step_duration_40hz=400, child_index=child, distribution=dist,
            )
            starts.append(reqs["brightness_raw"][0].timestep_40hz)
        expected = [seconds_to_timesteps(0.5 * i) for i in range(4)]
        self.assertEqual(expected, starts)
        self.assertEqual([0, 20, 40, 60], starts)


class CompilerGoboMultiWheelTest(unittest.TestCase):
    """Verify the compiler enumerates channels per the assignment's wheel_count."""

    def test_two_wheel_assignment_emits_both_channel_pairs(self) -> None:
        """Verify a two-wheel gobo assignment produces both slot and rotation channel pairs."""
        from unittest.mock import patch

        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.distribution import Distribution
        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
        from model.virtual_filters.property_cues.model.property_cue import PropertyCue
        from model.virtual_filters.property_cues.model.property_step import (
            ManualPropertyAssignment,
            PropertyAssignments,
            PropertyStep,
        )

        selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="FX")],
            enabled_capabilities={EnabledCapability.GOBO},
        )
        step = PropertyStep(name="s0", duration_40hz=40, assignments={
            "fixture:FX": PropertyAssignments(by_property={
                "gobo": ManualPropertyAssignment(
                    values={"wheel_count": 2, "slots": {0: 3, 1: 7}, "rotations": {0: 0.2, 1: -0.4}},
                    distribution=Distribution(),
                ),
            }),
        })
        model = PropertyCueFilterModel(
            fixture_selection=selection,
            cues=[PropertyCue(name="C1", steps=[step])],
        )
        with patch("model.virtual_filters.property_cues.compiler.build_postprocess_chain",
                   lambda cap, ctx: _passthrough_result(cap, ctx)):
            result = compile_property_model(model, "cuef", _StubScene())
        names = [ch for ch, _ in result.native_model.channels]
        self.assertIn("FX__goboslot_0", names)
        self.assertIn("FX__goborotation_0", names)
        self.assertIn("FX__goboslot_1", names)
        self.assertIn("FX__goborotation_1", names)


class _StubScene:
    pass


def _passthrough_result(cap: str, ctx):  # noqa: ANN001 - ad-hoc stub used by patch
    from model.virtual_filters.property_cues.postprocess import PostprocessOutput

    return PostprocessOutput(
        filters=(),
        external_ports={cap: (ctx.cue_filter_id, f"{ctx.channel_name_prefix}__{cap}")},
    )


class CompilerDefaultedChannelsTest(unittest.TestCase):
    """Defaulted channels are extracted to ``FILTER_CONSTANT_*`` filters.

    Verifies two layers of the optimization:

      1. A channel with no keyframes in any cue leaves the native cue
         filter's channel list entirely; a constant filter driven by
         the spec's ``default_value`` takes its place.
      2. When **every** raw input a post-processing strategy would read
         is defaulted and the strategy supports it, the whole chain
         folds down to a single constant. The dimmer strategy folds to
         one ``FILTER_CONSTANT_FLOAT`` when ``strobefreq`` is defaulted
         to zero (strobe generator with f=0 is a passthrough of
         brightness).
    """

    def _build_defaulted_dimmer_model(self):
        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
        from model.virtual_filters.property_cues.model.property_cue import PropertyCue
        from model.virtual_filters.property_cues.model.property_step import PropertyStep

        selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="FX")],
            enabled_capabilities={EnabledCapability.DIMMER},
        )
        # Cue with a step that doesn't dial any assignments; every dimmer
        # channel therefore stays at its spec default across all cues.
        return PropertyCueFilterModel(
            fixture_selection=selection,
            cues=[PropertyCue(name="C1", steps=[PropertyStep(name="s0", duration_40hz=40)])],
        )

    def test_defaulted_canonicals_leave_native_cue_filter(self) -> None:
        """Every dimmer channel stays at its default → native cue carries nothing dimmer-related."""
        from model.virtual_filters.property_cues.compiler import compile_property_model

        model = self._build_defaulted_dimmer_model()
        result = compile_property_model(model, "cuef", _StubScene())
        native_names = [ch for ch, _ in result.native_model.channels]
        for stripped in ("FX__brightness_raw", "FX__strobefreq", "FX__duty_cycle"):
            self.assertNotIn(
                stripped, native_names,
                f"defaulted channel {stripped!r} should not appear on the native cue filter; "
                f"it should have been replaced by a standalone constant filter",
            )

    def test_fully_defaulted_dimmer_folds_to_one_constant(self) -> None:
        """Strobe chain collapses to a single float constant."""
        from model.filter import FilterTypeEnumeration
        from model.virtual_filters.property_cues.compiler import compile_property_model

        model = self._build_defaulted_dimmer_model()
        result = compile_property_model(model, "cuef", _StubScene())
        # No freq / duty adapters, no strobe generator -- the fold replaces
        # the whole three-filter chain with one constant.
        strobe_count = sum(
            1 for f in result.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_SERIES_STROBE_GENERATOR_FLOAT)
        )
        self.assertEqual(0, strobe_count, "folded dimmer must not instantiate a strobe generator")
        adapter_count = sum(
            1 for f in result.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_ARITHMETICS_FLOAT_TO_8BIT)
        )
        self.assertEqual(0, adapter_count, "folded dimmer must not instantiate freq/duty adapters")
        float_constants = [
            f for f in result.postprocess_filters
            if int(f.filter_type) == int(FilterTypeEnumeration.FILTER_CONSTANT_FLOAT)
        ]
        self.assertGreaterEqual(
            len(float_constants), 1,
            "expected at least one float constant to carry the folded brightness value",
        )
        # The vfilter's ``brightness`` external port must resolve to one
        # of the emitted constant filters rather than the native cue filter.
        port = result.external_ports.get("FX__brightness")
        self.assertIsNotNone(port)
        const_ids = {f.filter_id for f in float_constants}
        self.assertIn(
            port[0], const_ids,
            f"expected brightness to resolve to a folded constant, got {port!r}",
        )

    def test_defaulted_passthrough_capability_redirects_to_constant(self) -> None:
        """Verify defaulted passthrough ports resolve to the emitted constant filter.

        Passthrough strategies (focus / frost / gobo / colour) that end
        up referencing a defaulted cue-filter channel must have their
        exposed external port rewritten onto the constant filter the
        compiler emitted. Without the redirect, the serializer's
        channel_override_dict would map ``cue_fid:channel`` to itself and
        fish would reject the show with
        ``E006: ... corresponding output channel wasn't found``.
        """
        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
        from model.virtual_filters.property_cues.model.property_cue import PropertyCue
        from model.virtual_filters.property_cues.model.property_step import PropertyStep

        selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="FX")],
            enabled_capabilities={EnabledCapability.FOCUS},
        )
        model = PropertyCueFilterModel(
            fixture_selection=selection,
            cues=[PropertyCue(name="C1", steps=[PropertyStep(name="s0", duration_40hz=40)])],
        )
        result = compile_property_model(model, "cuef", _StubScene())
        # The native cue filter must not carry the defaulted focus channel.
        native_names = {ch for ch, _ in result.native_model.channels}
        self.assertNotIn("FX__focus", native_names)
        # The exposed ``FX__focus`` port must resolve to the constant
        # filter the compiler emitted, not back to the (now-absent)
        # native cue filter channel.
        port = result.external_ports.get("FX__focus")
        self.assertIsNotNone(port)
        self.assertNotEqual("cuef", port[0],
                            "defaulted focus port leaked back to the native cue filter")
        constant_ids = {f.filter_id for f in result.postprocess_filters}
        self.assertIn(
            port[0], constant_ids,
            f"defaulted focus port should resolve to a constant filter, got {port!r}",
        )


class CompilerColorSegmentTest(unittest.TestCase):
    """Verify the compiler threads ``color_segment_count_lookup`` all the way through."""

    def test_multi_segment_manual_assignment_emits_per_segment_channels(self) -> None:
        """Verify a multi-segment color assignment emits one channel per segment index."""
        from unittest.mock import patch

        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.distribution import Distribution
        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
        from model.virtual_filters.property_cues.model.property_cue import PropertyCue
        from model.virtual_filters.property_cues.model.property_step import (
            ManualPropertyAssignment,
            PropertyAssignments,
            PropertyStep,
        )

        selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="FX")],
            enabled_capabilities={EnabledCapability.COLOR},
        )
        step = PropertyStep(name="s0", duration_40hz=40, assignments={
            "fixture:FX": PropertyAssignments(by_property={
                "color": ManualPropertyAssignment(
                    values={"colors": {0: ColorHSI(0.0, 1.0, 1.0), 1: ColorHSI(240.0, 1.0, 1.0)}},
                    distribution=Distribution(),
                ),
            }),
        })
        model = PropertyCueFilterModel(
            fixture_selection=selection,
            cues=[PropertyCue(name="C1", steps=[step])],
        )
        with patch("model.virtual_filters.property_cues.compiler.build_postprocess_chain",
                   lambda cap, ctx: _passthrough_result(cap, ctx)):
            result = compile_property_model(
                model, "cuef", _StubScene(),
                color_segment_count_lookup=lambda _fid: 3,
            )
        # ``channel_specs`` holds the virtual (pre-consolidation) channels
        # that surface on the vfilter node; ``native_model.channels`` is
        # already collapsed by the channel consolidator and will drop
        # byte-identical streams.
        virtual = set(result.channel_specs.keys())
        self.assertIn("FX__color_0", virtual)
        self.assertIn("FX__color_1", virtual)
        self.assertIn("FX__color_2", virtual)
        self.assertNotIn("FX__color", virtual)

    def test_color_preset_replicates_across_segments(self) -> None:
        """Verify a single-channel colour preset replicates onto every segment.

        A single-channel colour preset applied to a 3-segment fixture
        must produce three identical ``color_N`` keyframe streams.
        """
        from unittest.mock import patch

        from model.virtual_filters.property_cues.compiler import compile_property_model
        from model.virtual_filters.property_cues.distribution import Distribution
        from model.virtual_filters.property_cues.model.fixture_selection import (
            EnabledCapability,
            FixtureSelection,
            FixtureSelectionEntry,
            SelectionEntryKind,
        )
        from model.virtual_filters.property_cues.model.model import PropertyCueFilterModel
        from model.virtual_filters.property_cues.model.property_cue import PropertyCue
        from model.virtual_filters.property_cues.model.property_step import (
            PresetPropertyAssignment,
            PropertyAssignments,
            PropertyStep,
        )
        from model.virtual_filters.property_cues.presets import (
            EffectPreset,
            PresetKeyFrameEntry,
        )

        preset = EffectPreset(
            name="OneShotRed",
            description="",
            applies_for="color",
            hints=(),
            kf_requests=(
                PresetKeyFrameEntry(duration_expr="1.0", channel_exprs={"color": "0.0,1.0,1.0"}),
            ),
            source_path="",
            is_builtin=False,
        )

        selection = FixtureSelection(
            entries=[FixtureSelectionEntry(kind=SelectionEntryKind.FIXTURE, id="BAR")],
            enabled_capabilities={EnabledCapability.COLOR},
        )
        step = PropertyStep(name="s0", duration_40hz=40, assignments={
            "fixture:BAR": PropertyAssignments(by_property={
                "color": PresetPropertyAssignment(
                    preset_id="OneShotRed",
                    hint_values={},
                    distribution=Distribution(),
                ),
            }),
        })
        model = PropertyCueFilterModel(
            fixture_selection=selection,
            cues=[PropertyCue(name="C1", steps=[step])],
        )
        with patch("model.virtual_filters.property_cues.compiler.build_postprocess_chain",
                   lambda cap, ctx: _passthrough_result(cap, ctx)):
            result = compile_property_model(
                model, "cuef", _StubScene(),
                preset_library={preset.name: preset},
                color_segment_count_lookup=lambda _fid: 3,
            )
        # The vfilter exposes one virtual port per segment, and the preset's
        # single colour stream is expanded onto each. Consolidation keeps
        # the three segments as distinct native channels because they are
        # semantically different ports on the same fixture; the
        # consolidator refuses to merge different local names even when
        # the streams happen to be byte-identical (otherwise the dimmer
        # strategy's internal references to raw channel names like
        # ``strobefreq`` would be collapsed away and fish would fail to
        # resolve them).
        virtual = set(result.channel_specs.keys())
        self.assertIn("BAR__color_0", virtual)
        self.assertIn("BAR__color_1", virtual)
        self.assertIn("BAR__color_2", virtual)
        # Each segment is its own canonical; the preset stream is replicated
        # onto each so downstream consumers can address them independently.
        for seg in ("BAR__color_0", "BAR__color_1", "BAR__color_2"):
            self.assertEqual(seg, result.consolidation.canonical(seg))


class PositionPropertyTest(unittest.TestCase):
    """Tests for PositionProperty channel specs and request generation."""

    def test_channel_specs(self) -> None:
        """Verify PositionProperty exposes pan/tilt value and curvesel channels."""
        specs = PositionProperty().channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "pan_value": DataType.DT_DOUBLE,
                "pan_curvesel": DataType.DT_8_BIT,
                "tilt_value": DataType.DT_DOUBLE,
                "tilt_curvesel": DataType.DT_8_BIT,
            },
            names_to_types,
        )

    def test_curvesel_constant_across_children(self) -> None:
        """Verify the curvesel value is constant across children while delay still applies."""
        prop = PositionProperty(pan_value=0.5, pan_curvesel=CURVE_SIN, tilt_value=0.25)
        dist = Distribution(method=DistributionMethod.PHASE_LINEAR, phase_offset=0.25, amplitude=1.0)
        for child in range(3):
            reqs = prop.generate_requests(
                step_start_40hz=40, step_duration_40hz=200, child_index=child, distribution=dist,
            )
            self.assertEqual(CURVE_SIN, reqs["pan_curvesel"][0].requested_value)
            # Discrete channel still picks up the delay.
            expected_slot = 40 + seconds_to_timesteps(0.25 * child)
            self.assertEqual(expected_slot, reqs["pan_curvesel"][0].timestep_40hz)
            self.assertEqual(expected_slot, reqs["pan_value"][0].timestep_40hz)


class ColorPropertyTest(unittest.TestCase):
    """Tests for ColorProperty channel specs and request generation."""

    def test_channel_specs_single_segment(self) -> None:
        """Verify a single-segment ColorProperty exposes a lone ``color`` channel."""
        specs = ColorProperty().channel_specs
        self.assertEqual(("color",), tuple(s.name for s in specs))
        self.assertEqual(DataType.DT_COLOR, specs[0].data_type)

    def test_channel_specs_multi_segment(self) -> None:
        """Verify multi-segment ColorProperty exposes one channel per segment index."""
        specs = ColorProperty(segment_count=3).channel_specs
        self.assertEqual(("color_0", "color_1", "color_2"), tuple(s.name for s in specs))

    def test_discrete_value_unchanged_across_children(self) -> None:
        """Verify the authored colour is constant across children while timesteps shift."""
        colour = ColorHSI(120.0, 1.0, 0.5)
        prop = ColorProperty(colors={0: colour}, transition=TransferFunction.EDGE)
        dist = Distribution(method=DistributionMethod.PHASE_SIN, phase_offset=math.pi / 2, amplitude=1.0)
        values: list = []
        slots: list[int] = []
        for child in range(4):
            reqs = prop.generate_requests(
                step_start_40hz=200, step_duration_40hz=200, child_index=child, distribution=dist,
            )
            self.assertEqual(1, len(reqs["color"]))
            values.append(reqs["color"][0].requested_value)
            slots.append(reqs["color"][0].timestep_40hz)
        self.assertTrue(all(v == colour for v in values))
        # Delay is applied to the slot even on discrete channels.
        self.assertNotEqual(slots[0], slots[1])


class ColorDistributionTest(unittest.TestCase):
    """Verify the K colours → N segments spread rule.

    Per the user-specified behaviour:
      * K == 1       → same colour on every segment
      * 1 < K < N    → segment i gets ``authored[i * K // N]``
      * K >= N       → first N authored colours used
      * K == 0       → black everywhere
    """

    def test_empty_authored_fills_black(self) -> None:
        """Verify an empty authored map produces a black HSI triple for every slot."""
        result = distribute_colors({}, 3)
        self.assertEqual(3, len(result))
        # ``ColorHSI`` has no ``__eq__``, so compare field-by-field to
        # confirm each slot is a black HSI triple.
        for c in result:
            self.assertEqual(0.0, c.hue)
            self.assertEqual(0.0, c.saturation)
            self.assertEqual(0.0, c.intensity)

    def test_single_to_many_replicates_same_color(self) -> None:
        """Verify a single authored colour is replicated across every segment."""
        red = ColorHSI(0.0, 1.0, 1.0)
        result = distribute_colors({0: red}, 4)
        self.assertEqual([red, red, red, red], result)

    def test_two_to_four_blocks_even(self) -> None:
        """Verify two authored colours spread evenly as two blocks across four segments."""
        red = ColorHSI(0.0, 1.0, 1.0)
        blue = ColorHSI(240.0, 1.0, 1.0)
        result = distribute_colors({0: red, 1: blue}, 4)
        self.assertEqual([red, red, blue, blue], result)

    def test_three_to_four_floor_distribution(self) -> None:
        """Verify three authored colours spread across four segments using the floor rule."""
        red = ColorHSI(0.0, 1.0, 1.0)
        green = ColorHSI(120.0, 1.0, 1.0)
        blue = ColorHSI(240.0, 1.0, 1.0)
        result = distribute_colors({0: red, 1: green, 2: blue}, 4)
        # floor(i * 3 / 4): 0, 0, 1, 2
        self.assertEqual([red, red, green, blue], result)

    def test_more_authored_than_segments_uses_first_n(self) -> None:
        """Verify the first N authored colours are used when K exceeds segment count."""
        red = ColorHSI(0.0, 1.0, 1.0)
        green = ColorHSI(120.0, 1.0, 1.0)
        blue = ColorHSI(240.0, 1.0, 1.0)
        white = ColorHSI(0.0, 0.0, 1.0)
        result = distribute_colors({0: red, 1: green, 2: blue, 3: white}, 2)
        self.assertEqual([red, green], result)

    def test_color_property_multi_segment_requests(self) -> None:
        """Verify ColorProperty routes authored colours through distribute_colors across requests."""
        red = ColorHSI(0.0, 1.0, 1.0)
        blue = ColorHSI(240.0, 1.0, 1.0)
        prop = ColorProperty(segment_count=4, colors={0: red, 1: blue})
        reqs = prop.generate_requests(
            step_start_40hz=0, step_duration_40hz=40, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual({"color_0", "color_1", "color_2", "color_3"}, set(reqs.keys()))
        self.assertEqual(red, reqs["color_0"][0].requested_value)
        self.assertEqual(red, reqs["color_1"][0].requested_value)
        self.assertEqual(blue, reqs["color_2"][0].requested_value)
        self.assertEqual(blue, reqs["color_3"][0].requested_value)


class GoboPropertyTest(unittest.TestCase):
    """Tests for GoboProperty channel specs and request generation."""

    def test_channel_specs_single_wheel(self) -> None:
        """Verify a single-wheel GoboProperty exposes one slot/rotation channel pair."""
        specs = GoboProperty(wheel_count=1).channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {"goboslot_0": DataType.DT_8_BIT, "goborotation_0": DataType.DT_DOUBLE},
            names_to_types,
        )

    def test_channel_specs_two_wheels(self) -> None:
        """Verify a two-wheel GoboProperty exposes two slot/rotation channel pairs."""
        specs = GoboProperty(wheel_count=2).channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "goboslot_0": DataType.DT_8_BIT,
                "goborotation_0": DataType.DT_DOUBLE,
                "goboslot_1": DataType.DT_8_BIT,
                "goborotation_1": DataType.DT_DOUBLE,
            },
            names_to_types,
        )

    def test_requests_two_wheels(self) -> None:
        """Verify request generation across two wheels emits one request per channel."""
        prop = GoboProperty(wheel_count=2, slots={0: 3, 1: 5}, rotations={0: 0.25, 1: -0.5})
        reqs = prop.generate_requests(
            step_start_40hz=10, step_duration_40hz=100, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual({"goboslot_0", "goborotation_0", "goboslot_1", "goborotation_1"}, set(reqs.keys()))
        self.assertEqual(3, reqs["goboslot_0"][0].requested_value)
        self.assertEqual(5, reqs["goboslot_1"][0].requested_value)
        self.assertEqual(0.25, reqs["goborotation_0"][0].requested_value)
        self.assertEqual(-0.5, reqs["goborotation_1"][0].requested_value)


class BeamPropertyTest(unittest.TestCase):
    """Tests for BeamProperty channel specs and request generation."""

    def test_channel_specs_default_includes_all_sub_caps(self) -> None:
        """Verify default BeamProperty exposes zoom, prism, and iris channels."""
        specs = BeamProperty().channel_specs
        names_to_types = {s.name: s.data_type for s in specs}
        self.assertEqual(
            {
                "zoom": DataType.DT_8_BIT,
                "prism_selection": DataType.DT_8_BIT,
                "prism_rotation": DataType.DT_DOUBLE,
                "iris": DataType.DT_8_BIT,
            },
            names_to_types,
        )

    def test_channel_specs_omits_disabled_sub_caps(self) -> None:
        """Opting out of iris + prism (e.g. wash fixture with only zoom) drops those channels."""
        specs = BeamProperty(include_iris=False, include_prism=False).channel_specs
        names = {s.name for s in specs}
        self.assertEqual({"zoom"}, names)

    def test_values_round_trip(self) -> None:
        """Verify authored BeamProperty values round-trip into request values."""
        prop = BeamProperty(zoom=200, prism_selection=3, prism_rotation=0.9, iris=42)
        reqs = prop.generate_requests(
            step_start_40hz=0, step_duration_40hz=100, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(200, reqs["zoom"][0].requested_value)
        self.assertEqual(3, reqs["prism_selection"][0].requested_value)
        self.assertEqual(0.9, reqs["prism_rotation"][0].requested_value)
        self.assertEqual(42, reqs["iris"][0].requested_value)


class FocusPropertyTest(unittest.TestCase):
    """Tests for FocusProperty channel specs and request generation."""

    def test_focus_property_has_single_channel(self) -> None:
        """Verify FocusProperty exposes a single ``focus`` channel and round-trips values."""
        from model.virtual_filters.property_cues.properties import FocusProperty

        specs = FocusProperty().channel_specs
        self.assertEqual(1, len(specs))
        self.assertEqual("focus", specs[0].name)
        self.assertEqual(DataType.DT_8_BIT, specs[0].data_type)
        reqs = FocusProperty(focus=42).generate_requests(
            step_start_40hz=0, step_duration_40hz=100, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(42, reqs["focus"][0].requested_value)


class FrostPropertyTest(unittest.TestCase):
    """Tests for FrostProperty channel specs and request generation."""

    def test_channel_specs(self) -> None:
        """Verify FrostProperty exposes a single ``frost_intensity`` 8-bit channel."""
        specs = FrostProperty().channel_specs
        self.assertEqual(("frost_intensity",), tuple(s.name for s in specs))
        self.assertEqual(DataType.DT_8_BIT, specs[0].data_type)

    def test_request_value_type(self) -> None:
        """Verify FrostProperty request value preserves integer type for the 8-bit channel."""
        prop = FrostProperty(frost_intensity=128)
        reqs = prop.generate_requests(
            step_start_40hz=5, step_duration_40hz=20, child_index=0, distribution=_CONSTANT,
        )
        self.assertEqual(128, reqs["frost_intensity"][0].requested_value)
        self.assertIsInstance(reqs["frost_intensity"][0].requested_value, int)


if __name__ == "__main__":
    unittest.main()
