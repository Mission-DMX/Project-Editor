"""Fixture Definitions from OFL."""

# ruff: noqa: N815
from __future__ import annotations

from enum import Enum
from logging import getLogger
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from model.color_hsi import ColorHSI
from model.ofl.color_name_dict import get_color_by_name

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


class CapabilityType(Enum):
    """Defines the capability type as used by OFL."""

    NO_FUNCTION = "NoFunction"
    GENERIC = "Generic"
    SHUTTER_STROBE = "ShutterStrobe"
    STROBE_SPEED = "StrobeSpeed"
    STROBE_DURATION = "StrobeDuration"
    INTENSITY = "Intensity"
    COLOR_INTENSITY = "ColorIntensity"
    COLOR_PRESET = "ColorPreset"
    COLOR_TEMPERATURE = "ColorTemperature"
    PAN = "Pan"
    PAN_CONTINUOUS = "PanContinuous"
    TILT = "Tilt"
    TILT_CONTINUOUS = "TiltContinuous"
    PAN_TILT_SPEED = "PanTiltSpeed"
    WHEEL_SLOT = "WheelSlot"
    WHEEL_SHAKE = "WheelShake"
    WHEEL_SLOT_ROTATION = "WheelSlotRotation"
    WHEEL_ROTATION = "WheelRotation"
    EFFECT = "Effect"
    EFFECT_SPEED = "EffectSpeed"
    EFFECT_DURATION = "EffectDuration"
    EFFECT_PARAMETER ="EffectParameter"
    SOUND_SENSITIVITY = "SoundSensitivity"
    BEAM_ANGLE = "BeamAngle"
    BEAM_POSITION = "BeamPosition"
    FOCUS = "Focus"
    ZOOM = "Zoom"
    IRIS = "Iris"
    IRIS_EFFECT = "IrisEffect"
    FROST = "Frost"
    FROST_EFFECT = "FrostEffect"
    PRISM = "Prism"
    PRISM_ROTATION = "PrismRotation"
    BLADE_INSERTION = "BladeInsertion"
    BLADE_ROTATION = "BladeRotation"
    BLADE_SYSTEM_ROTATION = "BladeSystemRotation"
    FOG = "Fog"
    FOG_OUTPUT = "FogOutput"
    FOG_TYPE = "FogType"
    ROTATION = "Rotation"
    SPEED = "Speed"
    TIME = "Time"
    MAINTENANCE = "Maintenance"


class Capability(BaseModel):
    """Capability of a channel."""

    dmxRange: tuple[int, int] = (0, 0)
    """Defines the range in which this capability is active."""

    type: CapabilityType = CapabilityType.GENERIC
    """Capability type."""

    comment: str = ""
    """Description of the capability if not obvious."""

    capabilityProperties: dict[str, Any] = {}
    """Contains the properties of the capability."""

    def __init__(self, **kwargs: dict[str, Any]) -> None:
        """Overrides default constructor and populates capability settings."""
        super().__init__(**kwargs)

        if "capabilityProperties" in kwargs:
            raise ValueError("Fixme: this should not be a property of the OFL JSON model.")

        # This is an ugly hack. Once we know how to deal with the fact that the capabilities are only available based
        # on the specified type, we should improve this.
        for k, v in kwargs.items():
            if k not in ["type", "comment", "dmxRange"]:
                self.capabilityProperties[k] = v


class ChannelTemplate(BaseModel):
    """Capability templates of channel."""

    fineChannelAliases: list[str] | None = None
    """Channels matching this name will be associated as a file channel for this template."""

    capabilities: list[Capability] = []
    """The capabilities of this channel."""

    capability: Capability | None = None
    """If this channel has only a single capability, this will be set and capabilities left empty"""

    switchChannels: dict[str, str] = {}
    """Defines possible functionality switches based on the value of other channels."""

    defaultValue: int | str = 0
    """The default DMX value that should be output. If a string is found, if is most likely a number followed by %."""

    dmxValueResolution: str = "8bit"
    """Defines the resolution of the channel. This might be 8bit 16bit or 24bit."""

    def get_capabilities(self) -> list[Capability]:
        """A unified method to access the capabilities."""
        if len(self.capabilities) > 0:
            return self.capabilities
        return [self.capability] if self.capability is not None else []


class WheelSlotType(Enum):
    """The type of wheel slot."""

    GENERIC = ""
    OPEN = "Open"
    COLOR = "Color"
    GOBO = "Gobo"
    ANIMATED_GOBO_START = "AnimationGoboStart"
    ANIMATED_GOBO_END = "AnimationGoboEnd"
    IRIS = "Iris"
    PRISM = "Prism"
    FROST = "Frost"
    CLOSED = "Closed"


class WheelSlot(BaseModel):
    """Defines a rotatable wheel slot."""

    type: WheelSlotType = WheelSlotType.GENERIC
    """The type of wheel slot."""

    name: str = ""

    colorTemperature: str = ""

    resource: dict[str, Any] = {}
    """Contains the gobo image, if any."""

    colors: list[str] = []
    """Some fixtures contain a colors array instead of a name."""

    @property
    def resulting_color(self) -> ColorHSI:
        """Returns the color of the wheel slot."""
        # query color parameters and use name as last resort
        if self.type == WheelSlotType.OPEN:
            return get_color_by_name("white")
        if self.type == WheelSlotType.CLOSED:
            return get_color_by_name("black")
        if self.colorTemperature != "":
            return ColorHSI.from_color_temperature(self.colorTemperature)
        if len(self.colors) > 0:
            return get_color_by_name(self.colors[0])
        return get_color_by_name(self.name)


class Wheel(BaseModel):
    """Defines a rotatable wheel."""

    slots: list[WheelSlot] = []
    """The slots of the wheel."""


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

    availableChannels: dict[str, ChannelTemplate] = {}
    """Contains the capability mappings of the channels."""

    wheels: dict[str, Wheel] = {}
    """Containts the rotatable wheels"""

    model_config = ConfigDict(frozen=True)
