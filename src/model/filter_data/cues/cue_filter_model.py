"""Cue filter model."""

from model import DataType
from model.filter_data.cues.cue import Cue


class CueFilterModel:
    """Model of a cue filter configuration.

    Default Cue parameter encodes -1 as no default cue or 0 to n-1 as the index of the default cue.

    """

    def __init__(self, parameters: dict[str, str] | None = None) -> None:
        """Initialize empty model."""
        super().__init__()
        self.cues: list[Cue] = []
        self.channels: list[tuple[str, DataType]] = []  # name, data type
        self.global_restart_on_end: bool = False
        self._default_cue: int = -1

        if parameters is not None:
            self.load_from_configuration(parameters)

    @property
    def default_cue(self) -> int:
        """Default cue of filter.

        The default cue will be applied after switching to the scene of the filter (unless persistence rules
        kick in). The setter checks for reasonable values and will throw ValueError if they are invalid.

        """
        return self._default_cue

    @default_cue.setter
    def default_cue(self, val: int | str) -> None:
        new_value = int(val)
        if new_value < -1:
            raise ValueError("Cue value must be >= -1")
        if new_value >= len(self.cues):
            raise ValueError(f"Cue value must be < {len(self.cues)} (Due to number of cues).")
        self._default_cue = new_value

    def get_as_configuration(self) -> dict[str, str]:
        """Serialize filter configuration."""
        if len(self.cues) > 0:
            mapping_str = ";".join([f"{t[0]}:{t[1].format_for_filters()}" for t in self.cues[0].channels])
        else:
            mapping_str = ""
        return {"end_handling": "start_again" if self.global_restart_on_end else "hold", "mapping": mapping_str,
                "cuelist": "$".join([c.format_cue() for c in self.cues]), "default_cue": str(self.default_cue)}

    def append_cue(self, c: Cue) -> None:
        """Add a cue to the model."""
        if c not in self.cues:
            self.cues.append(c)
        for channel in self.channels:
            c.add_channel(channel[0], channel[1])

    def add_channel(self, name: str, dt: DataType) -> None:
        """Add a channel to the model."""
        for cd in self.channels:
            if name == cd[0]:
                if dt == cd[1]:
                    return
                raise ValueError("Channel names must be unique!")
        self.channels.append((name, dt))
        for c in self.cues:
            c.add_channel(name, dt)

    def remove_channel(self, c: tuple[str, DataType]) -> None:
        """Remove a channel from the model."""
        for cue in self.cues:
            cue.remove_channel(c)
        self.channels.remove(c)

    def load_from_configuration(self, parameters: dict[str, str]) -> None:
        """Deserialize configuration from filter configuration."""
        self.global_restart_on_end = parameters.get("end_handling") == "start_again"

        mapping_str = parameters.get("mapping")
        self.cues.clear()
        self.channels.clear()
        if mapping_str:
            for channel_dev in mapping_str.split(";"):
                splitted_channel_dev = channel_dev.split(":")
                self.channels.append((splitted_channel_dev[0], DataType.from_filter_str(splitted_channel_dev[1])))

        cuelist_definition_str = parameters.get("cuelist")
        cue_names = parameters.get("cue_names")
        cue_names = cue_names.split(";") if cue_names else []
        tmp_dict = {}
        for cue_name in cue_names:
            cue_split: list[str] = cue_name.split(":")
            tmp_dict[int(cue_split[1])] = cue_split[0]
        cue_names = tmp_dict
        if cuelist_definition_str:
            cue_definitions = cuelist_definition_str.split("$")
        else:
            return
        for i in range(len(cue_definitions)):
            c = Cue()
            c.name = cue_names.get(i)
            for cd in self.channels:
                c.add_channel(cd[0], cd[1])
            c.from_string_definition(cue_definitions[i])
            self.append_cue(c)

        if parameters.get("default_cue"):
            try:
                self.default_cue = int(parameters.get("default_cue"))
            except:
                self.default_cue = 0
