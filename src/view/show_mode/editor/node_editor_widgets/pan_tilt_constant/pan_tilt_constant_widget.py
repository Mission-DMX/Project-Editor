from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget, QCheckBox, QVBoxLayout

from model import Scene, BoardConfiguration
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import \
    PanTiltConstantContentWidget
# from view.show_mode.editor.nodes import FilterNode


class PanTiltConstantWidget(NodeEditorFilterConfigWidget):


    def __init__(self, filter_: PanTiltConstantFilter, parent: QWidget = None):
        super().__init__()
        self._filter = filter_
        self._parent_widget = QWidget(parent=parent)
        top_layout = QVBoxLayout()

        graph = PanTiltConstantContentWidget(self._filter, self._parent_widget)
        top_layout.addWidget(graph)
        self.cB8Bit = QCheckBox(self._parent_widget)
        self.cB16Bit = QCheckBox(self._parent_widget)
        self.cB8Bit.setText('8 Bit available')
        self.cB16Bit.setText('16 Bit available')
        self.cB8Bit.setChecked(self._filter.eight_bit_available)
        self.cB16Bit.setChecked(self._filter.sixteen_bit_available)
        top_layout.addWidget(self.cB8Bit)
        top_layout.addWidget(self.cB16Bit)
        self._parent_widget.setLayout(top_layout)

    def _get_configuration(self) -> dict[str, str]:
        return self._filter.filter_configurations

    def _load_configuration(self, conf: dict[str, str]):
        for key, value in conf.items():
            try:
                if key == 'outputs':
                    self._filter.filter_configurations['outputs'] = value
                else:
                    print('wrong key: ', key)
                    return False
            except:
                print('error parsing configuration, value: ', value, ' for param: ', key)
                return False
        return True

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        for key, value in parameters.items():
            try:
                if key == 'pan':
                    self._filter.pan = float(value)
                elif key == 'tilt':
                    self._filter.tilt = float(value)
                else:
                    print('wrong key: ', key)
                    return False
            except:
                print('error parsing parameter, value: ', value, ' for param: ', key)
                return False
        return True

    def _get_parameters(self) -> dict[str, str]:
        return {'pan': self._filter.pan,
                'tilt': self._filter.tilt}

    def parent_closed(self, filter_node: "FilterNode"):
        self._filter.update_allowed = False
        filter_node.outputs_changed(self.cB8Bit.isChecked(), self.cB16Bit.isChecked())

    def parent_opened(self):
        self._filter.update_allowed = True
        self.cB8Bit.setChecked(self._filter.eight_bit_available)
        self.cB16Bit.setChecked(self._filter.sixteen_bit_available)
