"""Fixture Definitions from OFL."""

# ruff: noqa: N815
from __future__ import annotations

from logging import getLogger
from typing import Literal

from pydantic import BaseModel, ConfigDict

logger = getLogger(__name__)


class MatrixChannelInsert(BaseModel):
    """Defines the order of pixels in a matrix used for automatic generation of channels."""
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


class FixtureMatrix(BaseModel):
    """Channel Repetition Matrix."""

    pixelCount: tuple[int, int, int] = [0, 0, 0]
    """Matrix Dimensions"""

    pixelKeys: list[str | None] | list[list[str | None] | None] | list[list[list[str | None] | None] | None] = []
    """Names of prefixes"""

    pixelGroup: list = []
    """Grouping of Pixels"""

    def generate_repetition_list(self, method: str) -> list[str]:
        """Generate a repetition list based on the matrix configuration.

        Args:
            method: The method for creation

        Returns:
            A ready-for-use list of repetition prefixes

        """
        repetition_list = []
        def resolve_list(obj: list | str, prefix: str = "") -> None:
            if isinstance(obj, str):
                if len(prefix) > 0:
                    prefix += " "
                repetition_list.append(prefix + obj)
            else:
                if obj is not None:
                    if len(obj) > 1:
                        if len(prefix) > 0:
                            prefix += ","
                        for i, x in enumerate(obj):
                            resolve_list(x, prefix=prefix + str(i))
                    else:
                        for x in obj:
                            resolve_list(x, prefix=prefix)
        match method:
            case "eachPixelABC":
                resolve_list(self.pixelKeys)
            case "eachPixelXYZ":
                for x in range(self.pixelCount[0]):
                    for y in range(self.pixelCount[1]):
                        repetition_list.extend([f"({x}, {y}, {z})" for z in range(self.pixelCount[2])])
            case "eachPixelXZY":
                for x in range(self.pixelCount[0]):
                    for z in range(self.pixelCount[2]):
                        repetition_list.extend([f"({x}, {y}, {z})" for y in range(self.pixelCount[1])])
            case "eachPixelYXZ":
                for y in range(self.pixelCount[1]):
                    for x in range(self.pixelCount[0]):
                        repetition_list.extend([f"({x}, {y}, {z})" for z in range(self.pixelCount[2])])
            case "eachPixelYZX":
                for y in range(self.pixelCount[1]):
                    for z in range(self.pixelCount[2]):
                        repetition_list.extend([f"({x}, {y}, {z})" for x in range(self.pixelCount[0])])
            case "eachPixelZXY":
                for z in range(self.pixelCount[2]):
                    for x in range(self.pixelCount[0]):
                        repetition_list.extend([f"({x}, {y}, {z})" for y in range(self.pixelCount[1])])
            case "eachPixelZYX":
                for z in range(self.pixelCount[2]):
                    for y in range(self.pixelCount[1]):
                        repetition_list.extend([f"({x}, {y}, {z})" for x in range(self.pixelCount[0])])
            case "eachPixelGroup":
                raise NotImplementedError("the constraints within pixel groups are very complicated and pixel groups "
                                          "are rarely used. Therefore this is not yet implemented. As you just got this"
                                          " error, it might be a good idea to start implementing them. Please provide "
                                          "fixture causing this.")
            case _:
                raise ValueError(f"Unknown generation method: {method}.")
        return repetition_list


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

    matrix: FixtureMatrix = FixtureMatrix()
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
