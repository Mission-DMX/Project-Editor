# coding=utf-8
"""Column fader filter nodes"""
from model import DataType
from model.control_desk import BankSet, BanksetIDUpdateListener
from model.filter import FilterTypeEnumeration

from view.show_mode.editor.nodes.base.filternode import FilterNode


class FaderRawNode(FilterNode):
    """Filter to represent any filter fader"""

    nodeName = "Raw"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_RAW, name=name, terminals={
            'primary': {'io': 'out'},
            'secondary': {'io': 'out'}
        })

        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except:
            self.filter.filter_configurations["column_id"] = ""

        # TODO search for linked bankset and register id update watcher
        set_id = self.filter.filter_configurations["set_id"]
        if self.filter.scene.linked_bankset.id == set_id:
            self._bankset_model = self.filter.scene.linked_bankset
        else:
            self._bankset_model = None
            for bs in BankSet.linked_bank_sets():
                if bs.id == set_id:
                    self._bankset_model = bs
                    break
            if not self._bankset_model:
                column_candidate = self.filter.scene.linked_bankset.get_column(self.filter.filter_configurations.get("column_id"))
                if column_candidate:
                    self.filter.filter_configurations["set_id"] = self.filter.scene.linked_bankset.id
                    self._bankset_model = self.filter.scene.linked_bankset

        if self._bankset_model:
            self._bankset_model.id_update_listeners.append(self)

        self.filter.out_data_types["primary"] = DataType.DT_16_BIT
        self.filter.out_data_types["secondary"] = DataType.DT_16_BIT

    def __del__(self):
        if self._bankset_model:
            self._bankset_model.id_update_listeners.remove(self)

    def notify_on_new_id(self, new_id: str):
        self.filter.filter_configurations["set_id"] = new_id


class FaderHSINode(FilterNode):
    """Filter to represent a hsi filter fader"""
    nodeName = "HSI"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSI, name=name, terminals={
            'color': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except:
            self.filter.filter_configurations["column_id"] = ""
        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations["ignore_main_brightness_control"]
        except:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR


class FaderHSIANode(FilterNode):
    """Filter to represent a hsia filter fader"""
    nodeName = "HSI-A"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=41, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except:
            self.filter.filter_configurations["column_id"] = ""
        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations["ignore_main_brightness_control"]
        except:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR
        self.filter.out_data_types["amber"] = DataType.DT_8_BIT


class FaderHSIUNode(FilterNode):
    """Filter to represent a hsiu filter fader"""
    nodeName = "HSI_U"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=42, name=name, terminals={
            'color': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except:
            self.filter.filter_configurations["column_id"] = ""
        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations["ignore_main_brightness_control"]
        except:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR
        self.filter.out_data_types["uv"] = DataType.DT_8_BIT


class FaderHSIAUNode(FilterNode):
    """Filter to represent a hasiau filter fader"""
    nodeName = "HSI-AU"

    def __init__(self, model, name):
        super().__init__(model=model, filter_type=43, name=name, terminals={
            'color': {'io': 'out'},
            'amber': {'io': 'out'},
            'uv': {'io': 'out'}
        })
        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except:
            self.filter.filter_configurations["column_id"] = ""
        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations["ignore_main_brightness_control"]
        except:
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
