from dataclasses import dataclass, field


@dataclass
class ChannelLink:
    input_channel_id: str
    output_channel_id: str


@dataclass
class FilterConfiguration:
    name: str
    value: str


@dataclass
class InitialParameter:
    name: str
    valie: str


@dataclass
class Filter:
    channel_links: list[ChannelLink] = field(default_factory=list)
    filter_configurations: list[FilterConfiguration] = field(default_factory=list)
    initial_parameters: list[InitialParameter] = field(default_factory=list)


def Constants8Bit() -> Filter:
    """Creates a filter for an 8 bit constant."""
    return Filter()


def ConstantsColor() -> Filter:
    """Creates a filter for a color filter."""
    return Filter()


def ColorToRGB() -> Filter:
    """Create a filter for a color to RGB converter."""
    return Filter()


def Universe() -> Filter:
    """Creates a filter for a universe."""
    return Filter()
