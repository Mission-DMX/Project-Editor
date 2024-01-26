from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget, QCheckBox, QVBoxLayout

from model import Scene, BoardConfiguration
from model.virtual_filters.pan_tilt_constant import PanTiltConstantFilter
from view.show_mode.editor.node_editor_widgets import NodeEditorFilterConfigWidget
from view.show_mode.editor.node_editor_widgets.pan_tilt_constant.pan_tilt_constant_content_widget import \
    PanTiltConstantContentWidget


class PanTiltConstantWidget(NodeEditorFilterConfigWidget):

    def _get_configuration(self) -> dict[str, str]:
        return {
            'pan': self._filter.pan,
            'tilt': self._filter.tilt,
            '8bit': self.cB8Bit.isChecked(),
            '16bit': self.cB16Bit.isChecked()
        }

    def _load_configuration(self, conf: dict[str, str]):
        for key, value in conf.items():
            try:
                if key == 'pan':
                    self._filter.pan = float(value)
                elif key == 'tilt':
                    self._filter.tilt = float(value)
                elif key == '8bit':
                    self._filter.eight_bit_available = bool(value)
                elif key == '16bit':
                    self._filter.sixteen_bit_available = bool(value)
                else:
                    print('wrong key: ', key)
                    return False
            except:
                print('error parsing value: ', value, ' for param: ', key)

    def get_widget(self) -> QWidget:
        return self._parent_widget

    def _load_parameters(self, parameters: dict[str, str]):
        pass

    def _get_parameters(self) -> dict[str, str]:
        return {'pan': '0.8', 'tilt': '01'}

    def __init__(self, parent: QWidget = None):
        super().__init__()
        self._parent_widget = QWidget(parent=parent)
        top_layout = QVBoxLayout()

        # just for now:
        scene = Scene(10, "tst", BoardConfiguration())
        self._filter = PanTiltConstantFilter(scene, filter_id="this new filter", filter_type=-2)

        graph = PanTiltConstantContentWidget(self._filter, self._parent_widget)
        top_layout.addWidget(graph)
        self.cB8Bit = QCheckBox(self._parent_widget)
        self.cB16Bit = QCheckBox(self._parent_widget)
        self.cB8Bit.setText('8 Bit available')
        self.cB16Bit.setText('16 Bit available')
        self.cB8Bit.setChecked(self._filter.eight_bit_available)
        self.cB16Bit.setChecked(self._filter.sixteen_bit_available)
        self.cB8Bit.stateChanged.connect(self.onCheckboxChange)
        self.cB16Bit.stateChanged.connect(self.onCheckboxChange)
        top_layout.addWidget(self.cB8Bit)
        top_layout.addWidget(self.cB16Bit)
        self._parent_widget.setLayout(top_layout)
    def onCheckboxChange(self):
        self._filter.eight_bit_available = self.cB8Bit.isChecked()
        self._filter.sixteen_bit_available = self.cB16Bit.isChecked()