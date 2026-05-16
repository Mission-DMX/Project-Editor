"""Contains chaser model."""

from enum import Enum
from typing import TYPE_CHECKING

from model.color_hsi import ColorHSI

if TYPE_CHECKING:
    from model.events import EventFilter


class ParameterType(Enum):
    """Describes the type of parameter."""

    NUMBER_ABSOLUTE = 0
    NUMBER_PERCENTAGE = 1
    COLOR = 2


class ChaserLayer:
    """Represents a chaser layer."""

    def __init__(
        self,
        type_description: str,
        variant_template: list[list[str]],
        parameter_template: list[tuple[str, ParameterType, str]],
        parameter_data: list[str],
    ) -> None:
        """Initialize the chaser layer.

        Args:
            type_description: The type prefix of the chaser layer.
            variant_template: If the type contains variants, each variant should be an entry in the list containing the
            choices.
            parameter_template: Each parameter represented by its name, its type and help text.
            parameter_data: The data of the parameters.

        """
        self.variant_template = variant_template
        self.variant_data: list[str] = type_description.split("__")
        self.layer_identifier = self.variant_data[0]
        self.variant_data.pop(0)
        self.parameter_templates: list[tuple[str, ParameterType, str]] = parameter_template
        self.parameter_data: list[str | ColorHSI | int] = []
        non_link_chars = [",", ".", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        for i, parameter in enumerate(parameter_data):
            parameter_str_copy = parameter
            for c in non_link_chars:
                parameter_str_copy = parameter_str_copy.replace(c, "")
            is_link = len(parameter_str_copy) > 0
            if is_link:
                self.parameter_data.append(parameter)
            else:
                template = parameter_template[i]
                if template[1] == ParameterType.COLOR:
                    self.parameter_data.append(ColorHSI.from_filter_str(parameter))
                else:
                    self.parameter_data.append(int(parameter))
        for i, variant_template in enumerate(self.variant_template):
            if i >= len(self.variant_data):
                self.variant_data.append(variant_template[0])

    def format_for_filters(self) -> str:
        """Serialize the chaser layer into a string representation."""
        parts = [self.layer_identifier + ("__" if len(self.variant_data) > 0 else "") + "__".join(self.variant_data)]
        for parameter in self.parameter_data:
            if isinstance(parameter, ColorHSI):
                parts.append(parameter.format_for_filter())
            elif isinstance(parameter, int):
                parts.append(str(parameter))
            else:
                parts.append(parameter)
        return "|".join(parts)


def construct_chaser_layer(identifier: str, parameter_data: list[str]) -> ChaserLayer:
    """Generate a new chaser layer from provided str description.

    Method guarantees existing parameter data.

    Args:
        identifier: The chaser layer identifier.
        parameter_data: The chaser layer parameter data.

    Returns:
        The chaser layer constructed from the provided parameters.

    """
    if identifier == "plain_color":
        layer = (ChaserLayer(identifier, [], [("Color", ParameterType.COLOR, "")], parameter_data))
    elif identifier == "rainbow":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [("Start Color", ParameterType.COLOR, ""), ("End Color", ParameterType.COLOR, "")],
                parameter_data,
            )
        )
    elif identifier == "sprinkles" or identifier == "dots":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [
                    ("Number of Sprinkles", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Sprinkle Size", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Update rate [ms]", ParameterType.NUMBER_ABSOLUTE, "0 = No Updates"),
                    (
                        "No dot value",
                        ParameterType.NUMBER_ABSOLUTE,
                        "The value the mask should obtain if there is no something at the given index",
                    ),
                    (
                        "dot value",
                        ParameterType.NUMBER_ABSOLUTE,
                        "The value the mask should obtain if there is a something at the given index",
                    ),
                ],
                parameter_data,
            )
        )
    elif identifier == "scale" or identifier == "scale_inv":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [
                    (
                        "cutoff-start",
                        ParameterType.NUMBER_ABSOLUTE,
                        "Where in the mask should the cutoff start?",
                    ),
                    ("cutoff-end", ParameterType.NUMBER_ABSOLUTE, "Where in the mask should the cutoff end?"),
                    ("mask-start-value", ParameterType.NUMBER_ABSOLUTE, "The beginning value of the mask."),
                    ("mask-end-value", ParameterType.NUMBER_ABSOLUTE, "The end value of the mask."),
                ],
                parameter_data,
            )
        )
    elif identifier == "flat_mask":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [("Mask value", ParameterType.NUMBER_ABSOLUTE, "The value to set on all mask entries.")],
                parameter_data,
            )
        )
    elif identifier == "mask_shift" or identifier == "color_shift":
        layer = (
            ChaserLayer(identifier, [], [("Shift period [ms]", ParameterType.NUMBER_ABSOLUTE, "")], parameter_data)
        )
    elif identifier.startswith("trig"):
        layer = (
            ChaserLayer(
                identifier,
                [["sin", "cos", "tan"]],
                [
                    ("Lowest value", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Highest value", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Phase", ParameterType.NUMBER_PERCENTAGE, ""),
                    (
                        "Frequency",
                        ParameterType.NUMBER_PERCENTAGE,
                        "1 period over whole mask → up to 1 period per entry",
                    ),
                ],
                parameter_data,
            )
        )
    elif identifier == "strobe":
        layer = (
            ChaserLayer(
                identifier, [], [("BPM", ParameterType.NUMBER_ABSOLUTE, "How Fast should it strobe?")], parameter_data
            )
        )
    elif identifier.startswith("maskmod"):
        layer = (
            ChaserLayer(
                identifier,
                [["add", "sub", "mul", "div"]],
                [("Modifier value", ParameterType.NUMBER_ABSOLUTE, "")],
                parameter_data,
            )
        )
    elif identifier.startswith("johnson"):
        layer = (
            ChaserLayer(
                identifier,
                [["rev", "fwd"]],
                [
                    ("Update speed [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Target mask value", ParameterType.NUMBER_ABSOLUTE, ""),
                ],
                parameter_data,
            )
        )
    elif identifier == "colormix":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [
                    ("Color A", ParameterType.COLOR, ""),
                    ("Color B", ParameterType.COLOR, ""),
                ],
                parameter_data,
            )
        )
    elif identifier.startswith("color_chanmod"):
        layer = (
            ChaserLayer(
                identifier,
                [["r", "g", "b", "h", "s", "i"]],
                [("Target Value", ParameterType.NUMBER_PERCENTAGE, "")],
                parameter_data,
            )
        )
    elif identifier.startswith("color_chancalc"):
        layer = (
            ChaserLayer(
                identifier,
                [["r", "g", "b", "h", "s", "i"], ["add", "sub", "mul", "div"]],
                [("Operand", ParameterType.NUMBER_PERCENTAGE, "")],
                parameter_data,
            )
        )
    elif identifier == "random_color":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [
                    ("Number of colors", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Update interval [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                ],
                parameter_data,
            )
        )
    elif identifier == "gaussian_blur":
        layer = (
            ChaserLayer(identifier, [], [("Filter size", ParameterType.NUMBER_PERCENTAGE, "")], parameter_data)
        )
    elif identifier == "gaussian_curve_on_mask":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [
                    ("Center position", ParameterType.NUMBER_PERCENTAGE, ""),
                    ("Width", ParameterType.NUMBER_PERCENTAGE, ""),
                    ("Height", ParameterType.NUMBER_PERCENTAGE, ""),
                ],
                parameter_data,
            )
        )
    elif identifier == "invert_color" or identifier == "invert_mask":
        layer = (ChaserLayer(identifier, [], [], parameter_data))
    elif identifier == "close_to_center" or identifier == "open_from_center":
        layer = (
            ChaserLayer(
                identifier,
                [],
                [
                    ("Update speed [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Decay rate", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Intensity", ParameterType.NUMBER_PERCENTAGE, ""),
                ],
                parameter_data,
            )
        )
    elif identifier.startswith(("segwave", "wave")):
        layer = (
            ChaserLayer(
                identifier,
                [["fwd", "rev"]],
                [
                    ("Update speed [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Decay rate", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Number of waves", ParameterType.NUMBER_ABSOLUTE, ""),
                    ("Intensity on Mask", ParameterType.NUMBER_PERCENTAGE, ""),
                ],
                parameter_data,
            )
        )
    else:
        raise ValueError(f"Unsupported layer identifier: {identifier}")
    for i in range(len(layer.parameter_data), len(layer.parameter_templates)):
        match layer.parameter_templates[i][1]:
            case ParameterType.NUMBER_PERCENTAGE | ParameterType.NUMBER_ABSOLUTE:
                layer.parameter_data.append(0)
            case ParameterType.COLOR:
                layer.parameter_data.append(ColorHSI(0.0, 0.0, 1.0))
            case _:
                raise NotImplementedError(f"Unexpected parameter type: {layer.parameter_templates[i][1]}")
    return layer


class ChaserConfig:
    """Represents an individual chaser configuration."""

    def __init__(self, filter_str: str) -> None:
        """Initialize the chaser configuration."""
        super().__init__()
        self.layers: list[ChaserLayer] = []
        for layer_str in filter_str.split(";"):
            if len(layer_str) == 0:
                continue
            parts = layer_str.split("|")
            identifier = parts[0]
            parts.pop(0)
            layer = construct_chaser_layer(identifier, parts)
            self.layers.append(layer)
        self._name = "NO NAME"

    @property
    def name(self) -> str:
        """Get or set the name of the preset config."""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    def format_for_filter_str(self) -> str:
        """Format the setup to be stored in a filter configuration."""
        layer_strings: list[str] = [layer.format_for_filters() for layer in self.layers]
        return ";".join(layer_strings)


class ChaserModel:
    """Contains representation of chaser configurations."""

    def __init__(self, config_parameter: dict[str, str]) -> None:
        """Initialize the model using the given configuration parameters.

        A default configuration must be set after the fact.

        Args:
            config_parameter: Configuration parameters as a dictionary to deserialize the model from.

        """
        self.number_of_pixels: int = int(config_parameter["number_of_pixels"])
        self.color_parameters: list[str] = config_parameter["color_parameters"].split(":") if (
                len(config_parameter["color_parameters"]) > 0) else []
        self.number_parameters: list[str] = config_parameter["number_parameters"].split(":") if (
                len(config_parameter["number_parameters"]) > 0) else []
        self.presets: list[ChaserConfig] = [ChaserConfig(s) for s in config_parameter["presets"].split("#")] if (
                len(config_parameter["presets"]) > 0) else []
        for i, name in enumerate(config_parameter.get("preset_names", "").split(";")):
            if i < len(self.presets):
                self.presets[i].name = name if name != "" else "NO NAME"
        self.default_config: ChaserConfig | None = None
        self.trigger_event: EventFilter | None = None

    def get_as_configuration(self) -> dict[str, str]:
        """Serializes the model into a set of configuration parameters.

        This does not include the default configuration.

        Returns:
            A dictionary with the required values filled in.

        """
        return {
            "number_of_pixels": str(self.number_of_pixels),
            "color_parameters": ":".join(self.color_parameters),
            "number_parameters": ":".join(self.number_parameters),
            "presets": "#".join(p.format_for_filter_str() for p in self.presets),
            "trigger_event": self.trigger_event.format_for_filters() if self.trigger_event is not None else "",
            "preset_names": ";".join(p.name for p in self.presets),
        }
