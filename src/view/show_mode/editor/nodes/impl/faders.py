# coding=utf-8
"""Column fader filter nodes"""
from typing import TYPE_CHECKING

from model import DataType
from model.control_desk import BankSet
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode

if TYPE_CHECKING:
    from model.filter import Filter
    from model.scene import Scene


class _FaderNode(FilterNode):
    def __init__(self, model: "Filter | Scene", filter_type: FilterTypeEnumeration, name: str, terminals: dict[str, dict[str, str]]):
        self._bankset_model: BankSet | None = None
        super().__init__(model=model, filter_type=filter_type, name=name, terminals=terminals)

        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except AttributeError:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except AttributeError:
            self.filter.filter_configurations["column_id"] = ""
        self._update_bankset_listener()

    def _update_bankset_listener(self):
        set_id = self.filter.filter_configurations["set_id"]

        if self.filter.scene.linked_bankset.id == set_id:
            self._bankset_model = self.filter.scene.linked_bankset
        else:
            for bs in BankSet.linked_bank_sets():
                if bs.id == set_id:
                    self._bankset_model = bs
                    break
            if self._bankset_model is None:
                column_candidate = self.filter.scene.linked_bankset.get_column(
                    self.filter.filter_configurations.get("column_id"))
                if column_candidate:
                    self.filter.filter_configurations["set_id"] = self.filter.scene.linked_bankset.id
                    self._bankset_model = self.filter.scene.linked_bankset

        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.append(self)

    def notify_on_new_id(self, new_id: str):
        self.filter.filter_configurations["set_id"] = new_id

    def update_node_after_settings_changed(self):
        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.remove(self)
        self._update_bankset_listener()

    def __del__(self):
        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.remove(self)


class FaderRawNode(_FaderNode):
    """Filter to represent any filter fader"""

    nodeName = "Raw"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_RAW, name=name, terminals={
            'primary': {'io': 'out'},
            'secondary': {'io': 'out'}
        })

        self.filter.out_data_types["primary"] = DataType.DT_16_BIT
        self.filter.out_data_types["secondary"] = DataType.DT_16_BIT


class FaderHSINode(_FaderNode):
    """Filter to represent a hsi filter fader"""
    nodeName = "HSI"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSI, name=name, terminals={
            'color': {'io': 'out'}
        })

        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations[
                "ignore_main_brightness_control"]
        except AttributeError:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR


class FaderHSIANode(_FaderNode):
    """Filter to represent a hsia filter fader"""
    nodeName = "HSI-A"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSIA, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'}
        })

        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations[
                "ignore_main_brightness_control"]
        except AttributeError:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR
        self.filter.out_data_types["amber"] = DataType.DT_8_BIT


class FaderHSIUNode(_FaderNode):
    """Filter to represent a hsiu filter fader"""
    nodeName = "HSI_U"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSIU, name=name, terminals={
            'color': {'io': 'out'},
            'uv': {'io': 'out'}
        })

        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations[
                "ignore_main_brightness_control"]
        except AttributeError:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR
        self.filter.out_data_types["uv"] = DataType.DT_8_BIT


class FaderHSIAUNode(_FaderNode):
    """Filter to represent a hasiau filter fader"""
    nodeName = "HSI-AU"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSIAU, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations[
                "ignore_main_brightness_control"]
        except AttributeError:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR
        self.filter.out_data_types["amber"] = DataType.DT_8_BIT
        self.filter.out_data_types["uv"] = DataType.DT_8_BIT


class FaderMainBrightness(FilterNode):
    """Filter to the main brightness fader"""
    nodeName = "global-ilumination"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS, name=name,
                         terminals={'brightness': {'io': 'out'}})

        self.filter.out_data_types["brightness"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False
