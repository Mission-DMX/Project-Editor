"""This file contains effects that provide generic numbers"""

from abc import ABC

from PySide6.QtWidgets import QWidget

from model import Filter
from model.curve_configuration import BaseCurve, CurveConfiguration
from model.filter import FilterTypeEnumeration
from model.virtual_filters.effects_stacks.adapters import emplace_with_adapter
from model.virtual_filters.effects_stacks.effect import Effect, EffectType
from view.utility_widgets.curve_editor import CurveEditorWidget


class GenericEffect(Effect, ABC):
    def get_output_slot_type(self) -> EffectType:
        return EffectType.GENERIC_NUMBER


class FunctionEffect(GenericEffect):
    """This effect implements the emplacement of generic curve functions"""

    def serialize(self) -> dict:
        return {"type": "generic.function",
                "config": self._widget.get_wave_config().serialize(),
                "phase_input": self._inputs["phase"].serialize() if self._inputs.get("phase") else "",
                "value_input": self._inputs["value"].serialize() if self._inputs.get("input") else "",
                }

    EFFECT_ID = "effect.animation.trigonometric_function"

    def get_serializable_effect_name(self) -> str:
        return self.EFFECT_ID

    def get_configuration_widget(self) -> QWidget | None:
        return self._widget

    def resolve_input_port_name(self, slot_id: str) -> str:
        match slot_id:
            case "phase":
                return "Phase"
            case "value":
                return "Input Value"
            case _:
                return slot_id

    def emplace_filter(self, filter_list: list[Filter], prefix: str) -> dict[str, str | list[str]]:
        latest_acc_filter_id = ""
        wc = self._widget.get_wave_config()

        zero_const = Filter(self.get_scene(), prefix + "_zero_const", FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                            self.get_position(), filter_configurations={}, initial_parameters={"value": "0.0"})
        filter_list.append(zero_const)
        one_const = Filter(self.get_scene(), prefix + "_one_const", FilterTypeEnumeration.FILTER_CONSTANT_FLOAT,
                           self.get_position(), filter_configurations={}, initial_parameters={"value": "1.0"})
        filter_list.append(one_const)

        value_input = self._inputs.get("input")
        if value_input:
            value_input_filter = emplace_with_adapter(value_input, EffectType.GENERIC_NUMBER,
                                                      filter_list, prefix + "_value_input__")["x"]
        else:
            value_input_filter = Filter(self.get_scene(), prefix + "_value_input",
                                        FilterTypeEnumeration.FILTER_TYPE_TIME_INPUT, self.get_position())
            # TODO this yields milliseconds. Is this reasonable?
            filter_list.append(value_input_filter)
            value_input_filter = value_input_filter.filter_id + ":value"

        phase_input = self._inputs.get("phase")
        if phase_input:
            base_phase_filter = emplace_with_adapter(phase_input, EffectType.GENERIC_NUMBER,
                                                     filter_list, prefix + "_base_phase__")["x"]
        else:
            base_phase_filter = Filter(self.get_scene(), f"{prefix}_base_phase",
                                       FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, self.get_position(),
                                       filter_configurations={}, initial_parameters={
                    "value": str(wc.base_phase),
                })
            filter_list.append(base_phase_filter)
            base_phase_filter = base_phase_filter.filter_id + ":value"

        for curve in [BaseCurve(2 ** c) for c in range(9)]:
            if wc.selected_features & curve > 0:
                c_filter_type = FilterTypeEnumeration.FILTER_TRIGONOMETRICS_SIN
                match curve:
                    case BaseCurve.COS:
                        c_filter_type = FilterTypeEnumeration.FILTER_TRIGONOMETRICS_COSIN
                    case BaseCurve.TAN:
                        c_filter_type = FilterTypeEnumeration.FILTER_TRIGONOMETRICS_TANGENT
                    case BaseCurve.ARC_SIN:
                        c_filter_type = FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCSIN
                    case BaseCurve.ARC_COS:
                        c_filter_type = FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCCOSIN
                    case BaseCurve.ARC_TAN:
                        c_filter_type = FilterTypeEnumeration.FILTER_TRIGONOMETRICS_ARCTANGENT
                    case BaseCurve.SAWTOOTH:
                        c_filter_type = FilterTypeEnumeration.FILTER_WAVES_SAWTOOTH
                    case BaseCurve.RECT:
                        c_filter_type = FilterTypeEnumeration.FILTER_WAVES_SQUARE
                    case BaseCurve.TRIANGLE:
                        c_filter_type = FilterTypeEnumeration.FILTER_WAVES_TRIANGLE
                curve_filter_id = prefix + "_" + str(curve.name)
                f_filter = Filter(self.get_scene(), curve_filter_id, c_filter_type, self.get_position(),
                                  initial_parameters={}, filter_configurations={})
                f_filter.channel_links["value_in"] = value_input_filter
                amplitude_filter = Filter(self.get_scene(), f"{prefix}_{curve.name}_amplitude",
                                          FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, self.get_position(),
                                          filter_configurations={}, initial_parameters={
                        "value": str(wc.base_amplitude * wc.amplitudes[curve]),
                    })
                filter_list.append(amplitude_filter)
                f_filter.channel_links["factor_outer"] = amplitude_filter.filter_id + ":value"
                if curve not in [BaseCurve.ARC_SIN, BaseCurve.ARC_COS, BaseCurve.ARC_TAN]:
                    f_filter.channel_links["phase"] = base_phase_filter
                    frequency_filter = Filter(self.get_scene(), f"{prefix}_{curve.name}_frequency",
                                              FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, self.get_position(),
                                              filter_configurations={}, initial_parameters={
                            "value": str(wc.frequencies[curve]),
                        })
                    filter_list.append(frequency_filter)
                    f_filter.channel_links["factor_inner"] = frequency_filter.filter_id + ":value"
                    offset_filter = Filter(self.get_scene(), f"{prefix}_{curve.name}_offset",
                                           FilterTypeEnumeration.FILTER_CONSTANT_FLOAT, self.get_position(),
                                           initial_parameters={"value": str(wc.offsets[curve])})
                    filter_list.append(offset_filter)
                    f_filter.channel_links["offset"] = offset_filter.filter_id + ":value"
                if latest_acc_filter_id == "":
                    latest_acc_filter_id = curve_filter_id
                else:
                    new_acc_filter_id = prefix + "_acc_" + str(curve.name)
                    acc_filter = Filter(self.get_scene(), new_acc_filter_id,
                                        FilterTypeEnumeration.FILTER_ARITHMETICS_MAC, self.get_position())
                    filter_list.append(acc_filter)
                    acc_filter.channel_links["factor1"] = one_const.filter_id + ":value" \
                        if wc.append_features_using_addition else latest_acc_filter_id + ":value"
                    acc_filter.channel_links["factor2"] = curve_filter_id + ":value"
                    acc_filter.channel_links["summand"] = latest_acc_filter_id + ":value" \
                        if wc.append_features_using_addition else zero_const.filter_id + ":value"
                    latest_acc_filter_id = new_acc_filter_id
                filter_list.append(f_filter)
        return {"x": latest_acc_filter_id + ":value"}

    def __init__(self) -> None:
        super().__init__({
            "phase": [EffectType.GENERIC_NUMBER],
            "input": [EffectType.GENERIC_NUMBER],
        })
        self._widget: CurveEditorWidget = CurveEditorWidget()
        self._widget.set_wave_config(CurveConfiguration())
        # TODO implement live update option

    def get_human_filter_name(self) -> str:
        return "Function"

    def get_description(self) -> str:
        return "This effect creates wave forms that it follows."

    def deserialize(self, data: dict[str, str | dict]) -> None:
        from model.virtual_filters.effects_stacks.effect_factory import effect_from_deserialization
        new_config = CurveConfiguration.from_str(data.get("config"))
        self._inputs["input"] = effect_from_deserialization(data["value_input"], self._parent_filter) \
            if data.get("value_input") else None
        self._inputs["phase"] = effect_from_deserialization(data["phase_input"], self._parent_filter) \
            if data.get("phase_input") else None
        self._widget.set_wave_config(new_config)
