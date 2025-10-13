"""Column fader filter nodes"""
from logging import getLogger

from model import DataType, Filter, Scene
from model.control_desk import BankSet
from model.filter import FilterTypeEnumeration
from model.virtual_filters.fader_vfilter import FaderUpdatingVFilter
from view.show_mode.editor.nodes.base.filternode import FilterNode

logger = getLogger(__name__)


class _FaderNode(FilterNode):
    def __init__(self, model: Filter | Scene, filter_type: FilterTypeEnumeration, name: str,
                 terminals: dict[str, dict[str, str]]) -> None:
        super().__init__(model=model, filter_type=filter_type, name=name, terminals=terminals)
        self._bankset_model: BankSet | None = self.filter.bankset_model if (
            isinstance(self.filter, FaderUpdatingVFilter)) else None

        try:
            self.filter.filter_configurations["set_id"] = model.filter_configurations["set_id"]
        except AttributeError:
            self.filter.filter_configurations["set_id"] = ""
        try:
            self.filter.filter_configurations["column_id"] = model.filter_configurations["column_id"]
        except AttributeError:
            self.filter.filter_configurations["column_id"] = ""

    def update_node_after_settings_changed(self) -> None:
        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.remove(self)
        if isinstance(self.filter, FaderUpdatingVFilter):
            self.filter.update_bankset_listener()
        else:
            logger.error("This fader filter has not been updated yet. Please save the show file and reload it NOW!")


class FaderRawNode(_FaderNode):
    """Filter to represent any filter fader"""

    nodeName = "Raw"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FADER_RAW, name=name, terminals={
            "primary": {"io": "out"},
            "secondary": {"io": "out"},
        })

        self.filter.out_data_types["primary"] = DataType.DT_16_BIT
        self.filter.out_data_types["secondary"] = DataType.DT_16_BIT


class FaderHSINode(_FaderNode):
    """Filter to represent a hsi filter fader"""
    nodeName = "HSI"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FADER_HSI, name=name, terminals={
            "color": {"io": "out"},
        })

        try:
            self.filter.filter_configurations["ignore_main_brightness_control"] = model.filter_configurations[
                "ignore_main_brightness_control"]
        except AttributeError:
            self.filter.filter_configurations["ignore_main_brightness_control"] = "false"

        self.filter.out_data_types["color"] = DataType.DT_COLOR


class FaderHSIANode(_FaderNode):
    """Filter to represent a hsia filter fader"""
    nodeName = "HSI-A"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FADER_HSIA, name=name, terminals={
            "color": {"io": "out"},
            "amber": {"io": "out"},
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
    nodeName = "HSI_U"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FADER_HSIU, name=name, terminals={
            "color": {"io": "out"},
            "uv": {"io": "out"},
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
    nodeName = "HSI-AU"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.VFILTER_FADER_HSIAU, name=name, terminals={
            "color": {"io": "out"},
            "amber": {"io": "out"},
            "uv": {"io": "out"},
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
    nodeName = "global-ilumination"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS, name=name,
                         terminals={"brightness": {"io": "out"}})

        self.filter.out_data_types["brightness"] = DataType.DT_16_BIT
        self.filter._configuration_supported = False
