"""Contains chaser model."""

from enum import Enum

from model import ColorHSI
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
        type_description,
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


# TODO introduce a dictionary containing layer_identifiers as key and human name, a description and GIF as value


class ChaserConfig:
    """Represents an individual chaser configuration."""

    def __init(self, filter_str: str) -> None:
        """Initialize the chaser configuration."""
        super().__init__()
        self.layers: list[ChaserLayer] = []
        for layer_str in filter_str.split(";"):
            parts = layer_str.split("|")
            identifier = parts[0]
            parts.pop(0)
            if identifier == "plain_color":
                self.layers.append(ChaserLayer(identifier, [], [("Color", ParameterType.COLOR, "")], parts))
            elif identifier == "rainbow":
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [],
                        [("Start Color", ParameterType.COLOR, ""), ("End Color", ParameterType.COLOR, "")],
                        parts,
                    )
                )
            elif identifier == "sprinkles" or identifier == "dots":
                self.layers.append(
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
                        parts,
                    )
                )
            elif identifier == "scale" or identifier == "scale_inv":
                self.layers.append(
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
                        parts,
                    )
                )
            elif identifier == "flat_mask":
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [],
                        [("Mask value", ParameterType.NUMBER_ABSOLUTE, "The value to set on all mask entries.")],
                        parts,
                    )
                )
            elif identifier == "mask_shift":
                self.layers.append(
                    ChaserLayer(identifier, [], [("Shift period [ms]", ParameterType.NUMBER_ABSOLUTE, "")], parts)
                )
            elif identifier == "color_shift":
                self.layers.append(
                    ChaserLayer(identifier, [], [("Shift period [ms]", ParameterType.NUMBER_ABSOLUTE, "")], parts)
                )
            elif identifier.startswith("trig"):
                self.layers.append(
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
                        parts,
                    )
                )
            elif identifier == "strobe":
                self.layers.append(
                    ChaserLayer(
                        identifier, [], [("BPM", ParameterType.NUMBER_ABSOLUTE, "How Fast should it strobe?")], parts
                    )
                )
            elif identifier.startswith("maskmod"):
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [["add", "sub", "mul", "div"]],
                        [("Modifier value", ParameterType.NUMBER_ABSOLUTE, "")],
                        parts,
                    )
                )
            elif identifier.startswith("johnson"):
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [["rev", "fwd"]],
                        [
                            ("Update speed [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Target mask value", ParameterType.NUMBER_ABSOLUTE, ""),
                        ],
                        parts,
                    )
                )
            elif identifier == "colormix":
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [],
                        [
                            ("Color A", ParameterType.COLOR, ""),
                            ("Color B", ParameterType.COLOR, ""),
                        ],
                        parts,
                    )
                )
            elif identifier.startswith("color_chanmod"):
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [["r", "g", "b", "h", "s", "i"]],
                        [("Target Value", ParameterType.NUMBER_PERCENTAGE, "")],
                        parts,
                    )
                )
            elif identifier.startswith("color_chancalc"):
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [["r", "g", "b", "h", "s", "i"], ["add", "sub", "mul", "div"]],
                        [("Operand", ParameterType.NUMBER_PERCENTAGE, "")],
                        parts,
                    )
                )
            elif identifier == "random_color":
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [],
                        [
                            ("Number of colors", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Update interval [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                        ],
                        parts,
                    )
                )
            elif identifier == "gaussian_blur":
                self.layers.append(
                    ChaserLayer(identifier, [], [("Filter size", ParameterType.NUMBER_PERCENTAGE, "")], parts)
                )
            elif identifier == "gaussian_curve_on_mask":
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [],
                        [
                            ("Center position", ParameterType.NUMBER_PERCENTAGE, ""),
                            ("Width", ParameterType.NUMBER_PERCENTAGE, ""),
                            ("Height", ParameterType.NUMBER_PERCENTAGE, ""),
                        ],
                        parts,
                    )
                )
            elif identifier == "invert_color" or identifier == "invert_mask":
                self.layers.append(ChaserLayer(identifier, [], [], parts))
            elif identifier == "close_to_center" or identifier == "open_from_center":
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [],
                        [
                            ("Update speed [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Decay rate", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Intensity", ParameterType.NUMBER_PERCENTAGE, ""),
                        ],
                        parts,
                    )
                )
            elif identifier.startswith("segwave") or identifier.startswith("wave"):
                self.layers.append(
                    ChaserLayer(
                        identifier,
                        [["fwd", "rev"]],
                        [
                            ("Update speed [ms]", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Decay rate", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Number of waves", ParameterType.NUMBER_ABSOLUTE, ""),
                            ("Intensity on Mask", ParameterType.NUMBER_PERCENTAGE, ""),
                        ],
                        parts,
                    )
                )
            else:
                raise ValueError(f"Unsupported layer identifier: {identifier}")


class ChaserModel:
    """Contains representation of chaser configurations."""

    def __init__(self, config_parameter: dict[str, str]):
        self.number_of_pixels = int(config_parameter["number_of_pixels"])
        self.color_parameters = config_parameter["color_parameters"].split(":")
        self.number_parameters = config_parameter["number_parameters"].split(":")
        self.presets: list[ChaserConfig] = [ChaserConfig(s) for s in config_parameter["presets"].split("#")]
        self.trigger_event: EventFilter | None = None
