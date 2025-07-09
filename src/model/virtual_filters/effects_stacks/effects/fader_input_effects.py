
"""This file defines effects that provide their output based on a selected input fader."""

from PySide6.QtWidgets import QWidget

from model import Filter
from model.control_desk import ColorDeskColumn
from model.filter import FilterTypeEnumeration
from model.virtual_filters.effects_stacks.effects.color_effects import ColorEffect
from view.show_mode.effect_stacks.configuration_widgets.fader_selection_configuration_widget import (
    FaderSelectionConfigurationWidget,
)


class ColorInputEffect(ColorEffect):

    def __init__(self) -> None:
        super().__init__({})
        self._fader: ColorDeskColumn | None = None
        self._ids_for_lazy_eval: tuple[str, str] = ("", "")

    def serialize(self) -> dict:
        return {"type": self.get_serializable_effect_name(),
                "fader_id": self._fader.id if self._fader is not None else self._ids_for_lazy_eval[1],
                "bankset_id": self._fader.bank_set.id if self._fader is not None else self._ids_for_lazy_eval[0]}

    def deserialize(self, data: dict[str, str]):
        self._ids_for_lazy_eval = (data.get("bankset_id") or "", data.get("fader_id") or "")
        if self.get_scene() is not None:
            self._resolve_fader()

    def _resolve_fader(self) -> None:
        # FIXME this does only look up the scenes bank set and ignores the stored bank set id
        scene = self.get_scene()
        if scene is not None:
            bankset = scene.linked_bankset
            if bankset is not None:
                self._fader = bankset.get_column(self._ids_for_lazy_eval[1])

    def get_configuration_widget(self) -> QWidget | None:
        if self._fader is None:
            self._resolve_fader()
        return FaderSelectionConfigurationWidget(self)

    def resolve_input_port_name(self, slot_id: str) -> str:
        return "invalid"  # As we have no inputs, this function does nothing

    def emplace_filter(self, filter_list: list[Filter], prefix: str) -> dict[str, str | list[str]]:
        if self._fader is None:
            self._resolve_fader()
        filter_id = prefix + "__hsi_fader"
        filter_list.append(Filter(self.get_scene(), filter_id, FilterTypeEnumeration.FILTER_FADER_HSI,
                                  self.get_position(),
                                  {"set_id": str(self._fader.bank_set.id),
                                   "column_id": str(self._fader.id),
                                   "ignore_main_brightness_control": "true"}))
        return {"color": filter_id + ":color"}

    def get_serializable_effect_name(self) -> str:
        return "color.InputFader"

    @property
    def fader(self) -> ColorDeskColumn:
        """Access the linked fader"""
        return self._fader

    @fader.setter
    def fader(self, new_fader: ColorDeskColumn) -> None:
        self._fader = new_fader
