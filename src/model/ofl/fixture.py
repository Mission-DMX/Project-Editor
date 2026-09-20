"""Fixture Definitions from OFL."""

from __future__ import annotations

import json
import math
import os
import random
from collections import defaultdict
from enum import IntFlag
from logging import getLogger
from typing import TYPE_CHECKING, Final
from uuid import UUID, uuid4

import numpy as np
from PySide6 import QtCore

from model.ofl.fixture_not_found_exception import FixtureDefNotFoundError
from model.ofl.ofl_fixture import CapabilityType, FixtureMode, MatrixChannelInsert, OflFixture, WheelSlot
from model.patching.fixture_channel import FixtureChannel, FixtureChannelType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from model import BoardConfiguration

logger = getLogger(__name__)


class ColorSupport(IntFlag):
    """Color Support of fixture."""

    NO_COLOR_SUPPORT = 0
    COLD_AND_WARM_WHITE = 1
    HAS_RGB_SUPPORT = 2
    HAS_WHITE_SEGMENT = 4
    HAS_AMBER_SEGMENT = 8
    HAS_UV_SEGMENT = 16

    def __str__(self) -> str:
        """Generate human-readable channel color support representation."""
        if self == ColorSupport.NO_COLOR_SUPPORT:
            return "No Color Support"
        s = []
        if (self & ColorSupport.COLD_AND_WARM_WHITE) > 0:
            s.append("CW/WW")
        if (self & ColorSupport.HAS_RGB_SUPPORT) > 0:
            s.append("RGB")
        if (self & ColorSupport.HAS_WHITE_SEGMENT) > 0:
            s.append("W")
        if (self & ColorSupport.HAS_AMBER_SEGMENT) > 0:
            s.append("A")
        if (self & ColorSupport.HAS_UV_SEGMENT) > 0:
            s.append("U")
        return "+".join(s)


def load_fixture(file: str) -> OflFixture:
    """Load fixture from OFL JSON."""
    if not os.path.isfile(file):
        logger.error("Fixture definition %s not found.", file)
        raise FixtureDefNotFoundError(file, "Path is no file. Does it exist?")
    with open(file, "r", encoding="UTF-8") as f:
        try:
            ob: dict = json.load(f)
        except json.decoder.JSONDecodeError as e:
            logger.error("Fixture definition (%s) JSON error: %s", file, e)
            raise FixtureDefNotFoundError(file, f"The file is not valid JSON: {e}") from e
    ob.update({"fileName": _fixture_display_name(file)})
    return OflFixture.model_validate(ob)


def _fixture_display_name(file: str) -> str:
    """Extract the fixtures-directory-relative name from a fixture definition path.

    Keeps the full path as fallback for files outside a ``fixtures/`` directory so that
    absolute paths still round-trip through stage file serialization.
    """
    if "/fixtures/" in file:
        return file.split("/fixtures/", 1)[1]
    return file


def _load_colorwheel_mappings(
    f: OflFixture, channels: list[FixtureChannel]
) -> list[tuple[FixtureChannel, list[tuple[int, WheelSlot, WheelSlot | None]]]]:
    """Load color wheel mappings from OFL model."""
    outer_mapping_list = []
    for channel in channels:
        fcl: list[tuple[int, WheelSlot, WheelSlot | None]] = []
        if channel.type != FixtureChannelType.COLORWHEEL:
            continue
        if channel.channel_template is None:
            logger.error("The channel %s is a color wheel but the template was not found.", channel.name)
            continue
        color_wheel = f.wheels.get(channel.name)
        if color_wheel is None:
            logger.warning("The channel %s is has a color wheel but the wheel definition was not found.", channel.name)
            continue
        for capability in channel.channel_template.get_capabilities():
            if capability.type == CapabilityType.WHEEL_SLOT:
                slot_number = capability.capabilityProperties.get("slotNumber")
                if len(capability.dmxRange) > 1:
                    capability_dmx_value = int((capability.dmxRange[0] + capability.dmxRange[1]) / 2)
                else:
                    capability_dmx_value = capability.dmxRange[0]
                if isinstance(slot_number, int):
                    wheel_slot = color_wheel.slots[slot_number % len(color_wheel.slots)]
                    fcl.append((capability_dmx_value, wheel_slot, None))
                elif isinstance(slot_number, float):
                    wheel_slot_a = color_wheel.slots[math.floor(slot_number) % len(color_wheel.slots)]
                    wheel_slot_b = color_wheel.slots[math.ceil(slot_number) % len(color_wheel.slots)]
                    fcl.append((capability_dmx_value, wheel_slot_a, wheel_slot_b))
                else:
                    logger.warning("The channel %s: cannot interpret slotNumber %r.", channel.name, slot_number)
        if len(fcl) > 0:
            outer_mapping_list.append((channel, fcl))
    return outer_mapping_list


def _parse_rotation_angle(value: object, channel_name: str, angle_key: str) -> float | None:
    """Parse an OFL rotation angle property into degrees.

    Returns:
        The angle in degrees, or ``None`` if no finite angle can be derived.

    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text == "infinite":
            logger.warning("Channel %s: %s is infinite; no finite rotation angle available.", channel_name, angle_key)
            return None
        if text.endswith("deg"):
            text = text.removesuffix("deg")
        try:
            return float(text)
        except ValueError:
            pass
    logger.warning("Channel %s: cannot interpret %s value %r as rotation angle.", channel_name, angle_key, value)
    return None


class UsedFixture(QtCore.QObject):
    """Fixture in use with a specific mode."""

    static_data_changed: QtCore.Signal = QtCore.Signal()

    def __init__(
        self,
        board_configuration: BoardConfiguration,
        fixture: OflFixture,
        mode_index: int,
        parent_universe: int,
        start_index: int,
        uuid: UUID | None = None,
        color: str | None = None,
    ) -> None:
        """Instantiate a UsedFixture object.

        Args:
            board_configuration: The show model
            fixture: The base fixture definition
            mode_index: The fixture mode to use
            parent_universe: The parent universe
            start_index: The first channels address
            uuid: The UUID of the fixture instance
            color: The color of the fixture in the patching view

        """
        super().__init__()
        self._board_configuration: Final[BoardConfiguration] = board_configuration
        self._fixture: Final[OflFixture] = fixture
        self._uuid: Final[UUID] = uuid or uuid4()

        self._start_index: int = start_index
        self._mode_index: int = mode_index
        self._universe_id: int = parent_universe

        channels, segment_map, color_support = self._generate_fixture_channels(fixture)

        self._fixture_channels: Final[list[FixtureChannel]] = channels
        self._segment_map: dict[FixtureChannelType, NDArray[np.int_]] = segment_map
        self._color_support: Final[ColorSupport] = color_support

        self._axis_movement_limits: Final[tuple[tuple[float, float], tuple[float, float]] | None] = (
            self._find_axis_movement_limits()
        )

        self._colorwheel_mappings: list[tuple[FixtureChannel, list[tuple[int, WheelSlot, WheelSlot | None]]]] = (
            _load_colorwheel_mappings(fixture, self._fixture_channels)
        )

        self._color_on_stage: str = (
            color or "#" + "".join([random.choice("0123456789ABCDEF") for _ in range(6)])  # noqa: S311 not a secret
        )
        self._name_on_stage: str = self.short_name or self.name

        self.parent_universe: int = parent_universe
        self._board_configuration.broadcaster.add_fixture.emit(self)

    @property
    def uuid(self) -> UUID:
        """UUID of the fixture."""
        return self._uuid

    @property
    def colorwheel_mappings(self) -> list[tuple[FixtureChannel, list[tuple[int, WheelSlot, WheelSlot | None]]]]:
        """Get the color wheels of this fixture.

        This list contains tuples of the channels that contain color wheels as well as their colors.
        Each slot is a tuple of the DMX value that should be send in order to get the color as well as the colors of the
        position. If the third parameter of this tuple is not None, the position is right in between two slots.

        Returns:
            A copy of the list.

        """
        return list(self._colorwheel_mappings)

    @property
    def power(self) -> float:
        """Fixture maximum continuous power draw (not accounting for capacitor charging as well as lamp warmup) in W."""
        return self._fixture.physical.power

    @property
    def name(self) -> str:
        """Name of theFixture."""
        return self._fixture.name

    @property
    def axis_movement_limits(self) -> tuple[tuple[float, float], tuple[float, float]] | None:
        """Get the pan/tilt axis limits as ``((pan_min, pan_max), (tilt_min, tilt_max))`` in degrees."""
        return self._axis_movement_limits

    @property
    def short_name(self) -> str:
        """Short name of theFixture."""
        return self._fixture.shortName

    @property
    def comment(self) -> str:
        """Comment of theFixture."""
        return self._fixture.comment

    @property
    def mode(self) -> FixtureMode:
        """Mode of theFixture.

        Raises:
            FixtureDefNotFoundError if the fixture mode does not exist.

        """
        if len(self._fixture.modes) <= self._mode_index:
            raise FixtureDefNotFoundError(
                self._fixture.fileName, "Fixture does not have requested mode. Are the fixture defintions up to date?"
            )
        return self._fixture.modes[self._mode_index]

    @property
    def start_index(self) -> int:
        """Start index of theFixture in the Universe indexed by 0."""
        return self._start_index

    @property
    def fixture_file(self) -> str:
        """File of the fixture."""
        return self._fixture.fileName

    @property
    def mode_index(self) -> int:
        """Index of the mode in the fixture."""
        return self._mode_index

    @property
    def universe_id(self) -> int:
        """Id of the universe for the fixture."""
        return self._universe_id

    @universe_id.setter
    def universe_id(self, universe_id: int) -> None:
        self._universe_id = universe_id

    @property
    def channel_length(self) -> int:
        """Number of channels of the fixture."""
        return len(self._fixture_channels)

    @property
    def channel_indexes(self) -> list[int]:
        """Index of the channels in the fixture."""
        return list(range(self._start_index, self._start_index + len(self._fixture_channels)))

    @property
    def fixture_channels(self) -> tuple[FixtureChannel, ...]:
        """Fixture channels of the fixture."""
        return tuple(self._fixture_channels)

    @property
    def color_on_stage(self) -> str:
        """Color of the fixture on stage."""
        return self._color_on_stage

    @color_on_stage.setter
    def color_on_stage(self, color: str) -> None:
        self._color_on_stage = color
        self.static_data_changed.emit()

    @property
    def name_on_stage(self) -> str:
        """Name of the fixture on stage."""
        return self._name_on_stage

    @name_on_stage.setter
    def name_on_stage(self, name: str) -> None:
        self._name_on_stage = name
        self.static_data_changed.emit()

    @property
    def color_support(self) -> ColorSupport:
        """Color support of the fixture."""
        return self._color_support

    def get_segment_in_universe_by_type(self, segment_type: FixtureChannelType) -> Sequence[int]:
        """Get a segment by type."""
        return tuple((self._segment_map[segment_type] + self.start_index).tolist())

    def _generate_fixture_channels(
        self, fixture_template: OflFixture
    ) -> tuple[list[FixtureChannel], dict[FixtureChannelType, NDArray[np.int_]], ColorSupport]:
        segment_map: dict[FixtureChannelType, list[int]] = defaultdict(list)
        fixture_channels: list[FixtureChannel] = []

        def append_channel(cn: str, i: int) -> None:
            channel = FixtureChannel(cn, fixture_template)
            fixture_channels.append(channel)
            for channel_type in channel.type_as_list:
                segment_map[channel_type].append(i)

        index = 0
        for channel_name in self.mode.channels:
            if isinstance(channel_name, MatrixChannelInsert):
                if isinstance(channel_name.repeatFor, list):
                    repetition_list = channel_name.repeatFor
                else:
                    repetition_list = self._fixture.matrix.generate_repetition_list(channel_name.repeatFor)
                for repeated_name in repetition_list:
                    for template_name in channel_name.templateChannels:
                        append_channel(template_name.replace("$pixelKey", "{}").format(repeated_name), index)
                        index += 1
            else:
                append_channel(channel_name if channel_name is not None else "", index)
                index += 1

        found_color = ColorSupport.NO_COLOR_SUPPORT
        if all(segment_map[t] for t in (FixtureChannelType.RED, FixtureChannelType.GREEN, FixtureChannelType.BLUE)):
            found_color |= ColorSupport.HAS_RGB_SUPPORT
        if segment_map[FixtureChannelType.UV]:
            found_color |= ColorSupport.HAS_UV_SEGMENT
        if segment_map[FixtureChannelType.AMBER]:
            found_color |= ColorSupport.HAS_AMBER_SEGMENT
        if segment_map[FixtureChannelType.WHITE]:
            found_color |= ColorSupport.HAS_WHITE_SEGMENT

        return (
            fixture_channels,
            {key: np.array(segment_map[key], dtype=np.int_) for key in FixtureChannelType},
            found_color,
        )

    def _find_axis_movement_limits(self) -> tuple[tuple[float, float], tuple[float, float]] | None:
        """Find the pan and tilt axis limits of the fixture in degrees.

        Pan/tilt channels whose angle properties cannot be interpreted as finite angles
        (``infinite``, percent values, missing properties) are skipped.

        Returns:
            ``((pan_min, pan_max), (tilt_min, tilt_max))`` in degrees, or ``None`` if no
            complete limits were found for both axes.

        """
        min_pan: float | None = None
        max_pan: float | None = None
        min_tilt: float | None = None
        max_tilt: float | None = None

        for channel in self._fixture_channels:
            template = channel.channel_template
            if template is None:
                logger.error("Channel %s has empty template.", channel.name)
                continue
            if channel.type == FixtureChannelType.PAN:
                is_pan = True
            elif channel.type == FixtureChannelType.TILT:
                is_pan = False
            else:
                continue
            if template.capability is not None:
                capability = template.capability
            elif template.capabilities:
                capability = template.capabilities[0]
            else:
                logger.error("Pan/Tilt channel %s has no capability description.", channel.name)
                continue
            cap_props = capability.capabilityProperties
            if "angleStart" not in cap_props or "angleEnd" not in cap_props:
                logger.error("Pan/Tilt channel %s does not have angle description.", channel.name)
                continue
            start = _parse_rotation_angle(cap_props["angleStart"], channel.name, "angleStart")
            end = _parse_rotation_angle(cap_props["angleEnd"], channel.name, "angleEnd")
            if start is None or end is None:
                continue
            if is_pan:
                min_pan = start if min_pan is None else min(min_pan, start)
                max_pan = end if max_pan is None else max(max_pan, end)
            else:
                min_tilt = start if min_tilt is None else min(min_tilt, start)
                max_tilt = end if max_tilt is None else max(max_tilt, end)

        if min_pan is None or max_pan is None or min_tilt is None or max_tilt is None:
            return None
        return (min_pan, max_pan), (min_tilt, max_tilt)

    def get_fixture_channel(self, index: int) -> FixtureChannel:
        """Get a fixture channel by index."""
        return self._fixture_channels[index]

    def __str__(self) -> str:
        """Get a human-readable description of the fixture in the show file."""
        return f"Fixture {self.name_on_stage or self.name} at {self.parent_universe}/{self.start_index}"


def make_used_fixture(
    board_configuration: BoardConfiguration, fixture: OflFixture, mode_index: int, universe_id: int, start_index: int
) -> UsedFixture:
    """Generate a new Used Fixture from a oflFixture."""
    try:
        return UsedFixture(board_configuration, fixture, mode_index, universe_id, start_index)
    except ValueError as e:
        logger.error(e)
        raise FixtureDefNotFoundError(fixture.fileName, str(e)) from e
