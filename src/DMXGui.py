import sys

from enum import Enum

from PySide6 import QtWidgets, QtGui, QtCore
from DMXModel import Channel, Universe


class Style(str, Enum):
    """Styles used throughout the app"""
    APP = ""
    WIDGET = ""
    SCROLL = """
    QScrollArea {
        border-style: outset;
        border-width: 1px;
        border-color: black;
    }
    """
    BUTTON = """
        border-style: outset;
        border-width: 1px;
        border-color: gray;
        border-radius : 5;
    """
    ACTIVE_BUTTON = "background-color : rgba(169,222,245,1); border-radius : 5;"
    SLIDER = ""


class MainWindow(QtWidgets.QMainWindow):
    """Main window of the app. All widget are children of its central widget"""

    def __init__(self, width: int = 1920, height: int = 1080):
        super().__init__()

        self.resize(width, height)
        self.setWindowTitle("Project-Editor")

        # DMX data. Each universe contains 512 channels
        self._universes: list[Universe] = [Universe(universe_id) for universe_id in range(4)]

        self.setCentralWidget(QtWidgets.QWidget(self))
        self.centralWidget().setFixedSize(self.size())
        layout = QtWidgets.QGridLayout(self.centralWidget())

        layout.setColumnStretch(376, 0)
        layout.setColumnStretch(376, 1)

        self._custom_editor: CustomEditorWidget = CustomEditorWidget(self._universes, parent=self.centralWidget())
        layout.addWidget(self._custom_editor, 0, 0, 1, 1)

        # QWidget to edit channels directly.
        self._direct_editor: DirectEditorWidget = DirectEditorWidget(self._universes, parent=self.centralWidget())
        layout.addWidget(self._direct_editor, 1, 0, 1, 2)

        self._setup_menubar()
        self._setup_toolbar()

    def _setup_menubar(self):
        """Adds a menubar with submenus"""
        self.setMenuBar(QtWidgets.QMenuBar())
        menuFile = QtWidgets.QMenu(self.menuBar())
        menuFile.setTitle("File")
        actionSave = QtGui.QAction(self)
        actionSave.setText("Save")
        actionSave.triggered.connect(self._save_scene)
        self.menuBar().addAction(menuFile.menuAction())
        menuFile.addAction(actionSave)

    def _setup_toolbar(self):
        """Adds a toolbar with actions"""
        toolbar = self.addToolBar("Mode")
        self.__switch_mode_action = QtGui.QAction(self)
        self.__switch_mode_action.setText("Direct Mode")
        self.__switch_mode_action.triggered.connect(self._switch_mode)
        toolbar.addAction(self.__switch_mode_action)

    def _switch_mode(self):
        """Switches between direct and filter mode"""
        current_mode = self.__switch_mode_action.text()
        if current_mode == "Direct Mode":
            self.__switch_mode_action.setText("Filter Mode")
        else:
            self.__switch_mode_action.setText("Direct Mode")

    def _save_scene(self):
        """Safes the current scene to a file
        TODO implement saving to xml file with xsd schema. See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd
        """
        pass


class CustomEditorWidget(QtWidgets.QTabWidget):
    """Widget to add and edit specific channels. Individual channels can be named."""

    def __init__(self, universes: list[Universe], parent=None):
        super().__init__(parent=parent)

        self._universes = universes
        self.setFixedSize(800, 500)

        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        self.addTab(CustomEditorTabWidget(universes), str(1))

        self.addTab(QtWidgets.QWidget(), "+")
        self.addTab(QtWidgets.QWidget(), "-")

        self.tabBarClicked.connect(self._tab_bar)

    def _tab_bar(self, index: int) -> None:
        if index == self.tabBar().count() - 2:
            text, ok = QtWidgets.QInputDialog.getText(self, "Add Custom Tab", "Tab Name")

            # TODO Create new tab and rearrange tab bar

        elif index == self.tabBar().count() - 1:
            text, ok = QtWidgets.QInputDialog.getText(self, "Remove Custom Tab", "Tab Name")

            # TODO Remove tab and rearrange tab bar


class CustomEditorTabWidget(QtWidgets.QWidget):
    """Widget for group of channels for CustomEditorWidget"""

    def __init__(self, universes: list[Universe], parent=None):
        super().__init__(parent=parent)

        self.testInt = 0

        self._channel_widgets: dict[ChannelWidget, str] = {}
        self._universes: list[Universe] = universes
        self.setFixedSize(752, 810)

        self._layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        self._layout.setColumnStretch(0, 400)
        self._layout.setColumnStretch(1, 400)
        for i in range(18):
            self._layout.setRowStretch(i, 30)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setVerticalSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)

        self._add_button = QtWidgets.QPushButton("+", self)
        self._add_button.setFixedSize(376, 30)
        self._add_button.clicked.connect(self._show_dialog)

        self._layout.addWidget(self._add_button, 0, 0, 1, 1)

        self.setLayout(self._layout)

    def _show_dialog(self):
        if len(self._channel_widgets) >= 16:
            return

        dlg = CustomEditorDialog()

        if dlg.exec():
            u_id, address, description = dlg.get_inputs()
            description = description if description != "" else f"Universe {u_id + 1} Channel {address + 1}"
            self._add_channel(self._universes[u_id].channels[address], description)

    def _add_channel(self, channel: Channel, description: str):
        channel_widget = ChannelWidget(channel, draw_horizontally=True)
        self._channel_widgets[channel_widget] = description

        self._layout.addWidget(channel_widget, len(self._channel_widgets), 0, 1, 1)

        label = QtWidgets.QLabel(description)
        label.setFixedSize(376, 30)
        self._layout.addWidget(label, len(self._channel_widgets), 3, 1, 1)


class CustomEditorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Choose a channel")

        layout = QtWidgets.QFormLayout(self)
        self._universe_label = QtWidgets.QLabel("Universe")
        self._universe_input = QtWidgets.QLineEdit()
        layout.addRow(self._universe_label, self._universe_input)

        self._channel_label = QtWidgets.QLabel("Channel")
        self._channel_input = QtWidgets.QLineEdit()
        layout.addRow(self._channel_label, self._channel_input)

        self._description_label = QtWidgets.QLabel("Description")
        self._description_input = QtWidgets.QLineEdit()
        layout.addRow(self._description_label, self._description_input)

        btnBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        layout.addWidget(btnBox)

        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)

    def get_inputs(self) -> tuple[int, int, str]:
        return int(self._universe_input.text()) - 1, int(self._channel_input.text()) - 1, self._description_input.text()


class DirectEditorWidget(QtWidgets.QTabWidget):
    """Widget to directly edit channels of one or multiple universes.
    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """

    def __init__(self, universes: list[Universe], parent=None):
        """Constructs a ManualUniverseEditorWidget"""
        super().__init__(parent=parent)

        # Move widget to the specified position with the specified size.
        self.setFixedSize(self.parent().width() - 50, 430)
        self.move(25, self.parent().height() - self.height() - 25)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        # Tabs left of the content
        self.setTabPosition(QtWidgets.QTabWidget.TabPosition.West)

        for universe in universes:

            # Scroll area left to right
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            scroll_area.setStyleSheet(Style.SCROLL)

            universe_widget = QtWidgets.QWidget()
            universe_widget.setLayout(QtWidgets.QHBoxLayout(universe_widget))

            # Add all channels of the universe
            for channel in universe.channels:
                universe_widget.layout().addWidget(ChannelWidget(channel))

            scroll_area.setWidget(universe_widget)

            # Add universe with tab name in human-readable form
            self.addTab(scroll_area, str(universe.address + 1))


class ChannelWidget(QtWidgets.QWidget):
    """Widget to edit a channel.
    Contains address label, value label, min/max buttons and slider.
    Slider allows to choose value between 0 and 255.
    Max button sets value to 255.
    Max button sets value to 0.
    Updates linked channel upon change and monitors linked channels updated signal.
    """

    def __init__(self, channel: Channel, draw_horizontally: bool = False, parent=None):
        super().__init__(parent=parent)

        # general width and height for all components
        element_size = 30

        # specific length of the slider
        slider_len = 256

        # The associated dmx channel
        self._channel: Channel = channel

        # Displays the address of the channel + 1 for human readability
        self._address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.address + 1), self)

        # Displays the current channel value
        self._value_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.value), self)

        # Button to set the channel to the max value 255
        self._max_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Max", self)

        # Slider to change the value and display the current value graphically
        direction = QtCore.Qt.Horizontal if draw_horizontally else QtCore.Qt.Vertical
        self._slider: QtWidgets.QSlider = QtWidgets.QSlider(direction, self)

        # Button to set the channel to the min value 0
        self._min_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Min", self)

        # Widget      Height
        # Address     30
        # Value       30
        # Max Button  30
        # Slider      256
        # Min Button  30

        self._channel.updated.connect(lambda x: self._update(x))

        # Offset to address_label -- value_label and value_label -- max/min button
        dx = element_size if draw_horizontally else 0
        dy = 0 if draw_horizontally else element_size

        self._address_label.setFixedSize(element_size, element_size)
        self._address_label.move(0, 0)
        self._address_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._value_label.setFixedSize(element_size, element_size)
        self._value_label.move(self._address_label.x() + dx, self._address_label.y() + dy)
        self._value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Slider format depending on if widget is vertical or horizontal
        slider_pos_x = (self._value_label.x() + 2 * dx) if draw_horizontally else 0
        slider_pos_y = 0 if draw_horizontally else (self._value_label.y() + 2 * dy)
        slider_width = slider_len if draw_horizontally else element_size
        slider_height = element_size if draw_horizontally else slider_len

        self._slider.setMinimum(0)
        self._slider.setMaximum(255)
        self._slider.setFixedSize(slider_width, slider_height)
        self._slider.move(slider_pos_x, slider_pos_y)
        self._slider.setStyleSheet(Style.SLIDER)
        self._slider.sliderMoved.connect(lambda x: self._channel.update(x))

        # Position of max and min button changes when the widget is shown horizontally
        max_btn_pos_x = (self._slider.x() + slider_len) if draw_horizontally else 0
        max_btn_pos_y = 0 if draw_horizontally else (self._value_label.y() + element_size)
        min_btn_pos_x = (self._value_label.x() + element_size) if draw_horizontally else 0
        min_btn_pos_y = 0 if draw_horizontally else (self._slider.y() + slider_len)

        self._max_button.setFixedSize(30, 30)
        self._max_button.move(max_btn_pos_x, max_btn_pos_y)
        self._max_button.setStyleSheet(Style.BUTTON)
        self._max_button.clicked.connect(lambda: self._channel.update(255))

        self._min_button.setFixedSize(30, 30)
        self._min_button.move(min_btn_pos_x, min_btn_pos_y)
        self._min_button.setStyleSheet(Style.ACTIVE_BUTTON)
        self._min_button.clicked.connect(lambda: self._channel.update(0))

        # Set widget position and size depending on its components and direction
        pos_x = (channel.address * 60) if draw_horizontally else 0
        pos_y = 0 if draw_horizontally else (channel.address * 60)
        width = self._value_label.width() + self._address_label.width() + self._max_button.width() + self._slider.width() + self._min_button.width() if draw_horizontally else 30
        height = 30 if draw_horizontally else self._value_label.height() + self._address_label.height() + self._max_button.height() + self._slider.height() + self._min_button.height()
        self.setFixedSize(width, height)
        self.move(pos_x, pos_y)
        self.setContentsMargins(0, 0, 0, 0)

    def _update(self, value: int) -> None:
        """Updates the slider and value label"""
        self._slider.setValue(value)
        self._value_label.setText(str(value))
        if value == 0:
            self._min_button.setStyleSheet(Style.ACTIVE_BUTTON)
            self._max_button.setStyleSheet(Style.BUTTON)
        elif value == 255:
            self._max_button.setStyleSheet(Style.ACTIVE_BUTTON)
            self._min_button.setStyleSheet(Style.BUTTON)
        else:
            self._min_button.setStyleSheet(Style.BUTTON)
            self._max_button.setStyleSheet(Style.BUTTON)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    screen_width = app.primaryScreen().size().width()
    screen_height = app.primaryScreen().size().height()
    widget = MainWindow(width=1920, height=1080)
    widget.show()

    sys.exit(app.exec())
