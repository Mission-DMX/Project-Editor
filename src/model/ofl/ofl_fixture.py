"""Fixture Definitions from OFL"""

# ruff: noqa: N815
from __future__ import annotations

from logging import getLogger
from typing import Literal

from pydantic import BaseModel, ConfigDict

logger = getLogger(__name__)


class MatrixChannelInsert(BaseModel):
    insert: Literal["matrixChannels"]
    repeatFor: str | list[str]

    channelOrder: Literal["perPixel", "perChannel"]
    templateChannels: list[str]

    model_config = ConfigDict(frozen=True)


class FixtureMode(BaseModel):
    """Defines one DMX mode for the fixture, including channel order."""

    name: str
    """Full name of the mode (e.g. '4-channel')."""

    shortName: str = ""
    """Short name of the mode (e.g. '4ch')."""

    #    rdmPersonalityIndex: int
    #    physical: Physical
    channels: list[str | MatrixChannelInsert | None]
    """List of channel names used in this mode."""

    model_config = ConfigDict(frozen=True)


class FixturePhysicalBulb(BaseModel):
    """Physical attributes of the fixture's light source."""

    type: str = ""
    """Type of light source, e.g. 'LED', 'Halogen'."""

    colorTemperature: int = 0
    """Color temperature in Kelvin."""

    lumens: float = 0
    """Light output in lumens."""

    model_config = ConfigDict(frozen=True)


class FixturePhysical(BaseModel):
    """Physical properties of the fixture housing and electronics."""

    dimensions: tuple[float, float, float] = [0.0, 0.0, 0.0]
    """Dimensions in millimeters (e.g. [width, height, depth])."""

    weight: float = 0
    """Weight in kilograms."""

    power: float = 0
    """Maximum power consumption in watts."""

    DMXconnector: str = ""
    """Type of DMX connector (e.g. '3-pin', '5-pin')."""

    bulb: FixturePhysicalBulb = FixturePhysicalBulb()
    """Details about the built-in light source."""

    model_config = ConfigDict(frozen=True)


class OflFixture(BaseModel):
    """Complete fixture definition conforming to the Open Fixture Library schema."""

    name: str
    """Name of the fixture."""

    shortName: str = ""
    """Short name of the fixture."""

    categories: list[str]
    """Categories this fixture belongs to (e.g. 'Dimmer', 'Moving Head')."""

    # meta: FixtureMeta
    # """Metadata including author and timestamps."""

    comment: str = ""
    """Description of the fixture."""

    # matrix: FixtureMatrix = FixtureMatrix
    # """Optional matrix layout and grouping, if the fixture has pixels."""

    # templateChannels: dict[str, TemplateChannel]] = {}
    # """Reusable channels defined with placeholders for matrix-based fixtures."""

    # availableChannels: dict[str, AvailableChannel] = {}
    # """All available DMX channels, keyed by name."""

    modes: list[FixtureMode]
    """DMX modes defining channel orders for different configurations."""

    # fixtureKey: str
    # """Unique key for the fixture (usually a slug)."""

    # manufacturerKey: str
    # """Slug identifying the manufacturer."""

    # oflURL: HttpUrl
    # """Link to the fixture's page on the Open Fixture Library website."""

    # links: FixtureLinks = FixtureLinks()
    # """Optional set of external links such as manuals and videos."""

    physical: FixturePhysical = FixturePhysical()
    """Physical data including weight, size, and connector type."""

    fileName: str
    """File name of the fixture.
    Extended
    """

    model_config = ConfigDict(frozen=True)
