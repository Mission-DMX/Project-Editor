from model import DataType
from view.show_mode.editor.node_editor_widgets.cue_editor.model.cue import Cue


class CueFilterModel:
    def __init__(self, parameters: dict[str, str] | None = None) -> None:
        super().__init__()
        self.cues: list[Cue] = []
        self.channels: list[tuple[str, DataType]] = []  # name, data type
        self.global_restart_on_end: bool = False
        self.default_cue: int = 0

        if parameters is not None:
            self.load_from_configuration(parameters)

    def get_as_configuration(self) -> dict[str, str]:
        if len(self.cues) > 0:
            mapping_str = ";".join([f"{t[0]}:{t[1].format_for_filters()}" for t in self.cues[0].channels])
        else:
            mapping_str = ""
        return {"end_handling": "start_again" if self.global_restart_on_end else "hold", "mapping": mapping_str,
                "cuelist": "$".join([c.format_cue() for c in self.cues]), "default_cue": self.default_cue}

    def append_cue(self, c: Cue) -> None:
        if c not in self.cues:
            self.cues.append(c)
        for channel in self.channels:
            c.add_channel(channel[0], channel[1])

    def add_channel(self, name: str, dt: DataType) -> None:
        for cd in self.channels:
            if name == cd[0]:
                if dt == cd[1]:
                    return
                raise ValueError("Channel names must be unique!")
        self.channels.append((name, dt))
        for c in self.cues:
            c.add_channel(name, dt)

    def remove_channel(self, c: tuple[str, DataType]) -> None:
        for cue in self.cues:
            cue.remove_channel(c)
        self.channels.remove(c)

    def load_from_configuration(self, parameters: dict[str, str]) -> None:
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
                self.default_cue = int(parameters.get("default_cue")) + 1
            except:
                self.default_cue = 0
