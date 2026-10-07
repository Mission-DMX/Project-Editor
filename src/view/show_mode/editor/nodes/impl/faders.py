"""Column fader filter nodes"""

from typing import override

from model import Filter, Scene
from model.control_desk import BankSet
from model.filter import FilterTypeEnumeration
from view.show_mode.editor.nodes.base.filternode import FilterNode


class _FaderNode(FilterNode):
    """Base node for the column-fader filters.

    Model-side state (``set_id`` / ``column_id`` defaults, I/O signature) lives on the
    registered Filter subclasses under :mod:`model.filters.faders`. The node itself only
    manages the BankSet listener subscription so that id renames propagate into the filter's
    configuration.
    """

    def __init__(self, model: Filter | Scene, filter_type: FilterTypeEnumeration, name: str) -> None:
        self._bankset_model: BankSet | None = None
        super().__init__(model=model, filter_type=filter_type, name=name)
        self._update_bankset_listener()

    def _update_bankset_listener(self) -> None:
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

    def notify_on_new_id(self, new_id: str) -> None:
        self.filter.filter_configurations["set_id"] = new_id

    @override
    def update_node_after_settings_changed(self) -> None:
        # Keep pyqtgraph terminals in sync with the (static) filter signature, then re-anchor
        # the BankSet listener in case the user picked a different bank set in the settings.
        super().update_node_after_settings_changed()
        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.remove(self)
            self._bankset_model = None
        self._update_bankset_listener()

    def __del__(self) -> None:
        if self._bankset_model is not None:
            self._bankset_model.id_update_listeners.remove(self)


class FaderRawNode(_FaderNode):
    """Filter to represent any filter fader"""

    nodeName = "Raw"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_RAW, name=name)


class FaderHSINode(_FaderNode):
    """Filter to represent a hsi filter fader"""
    nodeName = "HSI"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSI, name=name)


class FaderHSIANode(_FaderNode):
    """Filter to represent a hsia filter fader"""
    nodeName = "HSI-A"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSIA, name=name)


class FaderHSIUNode(_FaderNode):
    """Filter to represent a hsiu filter fader"""
    nodeName = "HSI_U"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSIU, name=name)


class FaderHSIAUNode(_FaderNode):
    """Filter to represent a hasiau filter fader"""
    nodeName = "HSI-AU"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_FADER_HSIAU, name=name)


class FaderMainBrightness(FilterNode):
    """Filter to the main brightness fader"""
    nodeName = "global-ilumination"  # noqa: N815

    def __init__(self, model: Filter, name: str) -> None:
        super().__init__(model=model, filter_type=FilterTypeEnumeration.FILTER_TYPE_MAIN_BRIGHTNESS, name=name)
