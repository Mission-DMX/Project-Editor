import sys

from enum import Enum
from PySide6 import QtWidgets, QtGui, QtCore
from DMXModel import Channel, Universe, ConnectionTest


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
        [ConnectionTest(universe) for universe in self._universes]

        self.setCentralWidget(QtWidgets.QWidget(self))
        self.centralWidget().setFixedSize(self.size())

        # QWidget to edit channels directly.
        self._manual_editor: ManualUniverseEditorWidget = ManualUniverseEditorWidget(self.centralWidget(),
                                                                                     self._universes)
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


class ManualUniverseEditorWidget(QtWidgets.QFrame):
    """Widget to directly edit channels of one or multiple universes.
    Allows editing of channels of the specified universes. One universe is shown and editable at a time.
    Buttons allow to change the selected universe.
    """

    def __init__(self, parent: QtWidgets.QWidget, universes: list[Universe]):
        """Constructs a ManualUniverseEditorWidget"""
        super().__init__(parent=parent)

        # Move widget to the specified position with the specified size. Max height is 500
        self.setFixedSize(self.parent().width() - 50, 500)
        self.move(25, self.parent().height() - 600)

        # Specifying style options. See Style.WIDGET
        self.setObjectName("ManualEditor")
        self.setStyleSheet(Style.WIDGET)

        ####################################
        # Setting up area for button to select a universe

        self._universe_selection_label: QtWidgets.QLabel = QtWidgets.QLabel(
            "Universes", self)
        self._universe_selection_label.setFixedSize(100, 20)
        self._universe_selection_label.move(0, 0)

        # QWidget used as parent for all selection elements
        self._universe_selection: QtWidgets.QWidget = QtWidgets.QWidget(self)
        self._universe_selection.setFixedSize(280, 50)
        self._universe_selection.move(0, self._universe_selection_label.y() + self._universe_selection_label.height())

        # QButtonGroup to group for all buttons
        self._universe_selection_group: QtWidgets.QButtonGroup = QtWidgets.QButtonGroup(self._universe_selection)
        self._universe_selection_group.buttonClicked.connect(self._set_active_universe)

        ####################################
        # Setting up area for channel slider and info

        self._universe_label: QtWidgets.QLabel = QtWidgets.QLabel("Channels", self)
        self._universe_label.setFixedSize(100, 20)
        self._universe_label.move(0, self._universe_selection.y() + self._universe_selection.height())

        # QStackedWidget to manage which universe is shown
        self._stacked_universes_widget: QtWidgets.QStackedWidget = QtWidgets.QStackedWidget()

        # QScrollArea to allow all 512 channels of a universe to be shown horizontally
        self._scroll_area: QtWidgets.QScrollArea = QtWidgets.QScrollArea(self)
        self._scroll_area.setFixedSize(self.width(), self.height() - (
                    self._universe_selection_label.height() + self._universe_selection.height() + self._universe_label.height()))
        self._scroll_area.move(0, self._universe_label.y() + self._universe_label.height())
        self._scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._scroll_area.setStyleSheet(Style.SCROLL)

        ####################################
        # Adding dmx universes and their channels to a QStackedWidget. The selected universe is shown on,
        # all the others are hidden

        for universe in universes:
            universe_widget = QtWidgets.QWidget()

            # The channels are arranged horizontally
            universe_widget.setLayout(QtWidgets.QHBoxLayout(universe_widget))

            # Add all channels of the universe
            for channel in universe.channels:
                universe_widget.layout().addWidget(ChannelWidget(channel))

            # Create selector button for the universe
            universe_selector = QtWidgets.QPushButton(str(universe.id + 1), self)
            universe_selector.setStyleSheet(Style.BUTTON)
            universe_selector.setFixedSize(30, 30)
            universe_selector.move(universe.id * 30,
                                   self._universe_selection_label.y() + self._universe_selection_label.height())

            self._universe_selection_group.addButton(universe_selector, universe.id)
            self._stacked_universes_widget.addWidget(universe_widget)

        self._scroll_area.setWidget(self._stacked_universes_widget)

        # Showing universe 0 by default
        self._set_active_universe(self._universe_selection_group.button(0))

    def _set_active_universe(self, selected_button: QtWidgets.QAbstractButton) -> None:
        """Change the currently shown universe to the selected"""
        universe_id = self._universe_selection_group.id(selected_button)
        self._stacked_universes_widget.setCurrentIndex(universe_id)
        # Resetting the style of all buttons
        for button in self._universe_selection_group.buttons():
            button.setStyleSheet(Style.BUTTON)
        selected_button.setStyleSheet(Style.ACTIVE_BUTTON)


class ChannelWidget(QtWidgets.QWidget):
    """Widget to edit a channel.
    Contains address label, value label, min/max buttons and slider.
    Slider allows to choose value between 0 and 255.
    Max button sets value to 255.
    Max button sets value to 0.
    Updates linked channel upon change and monitors linked channels updated signal.
    """

    def __init__(self, channel: Channel):
        super().__init__()

        self.setFixedSize(30, 356)
        self.move(channel.address * 60, 0)

        # The associated dmx channel
        self._channel: Channel = channel

        # Displays the address of the channel + 1 for human readability
        self._address_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.address + 1), self)

        # Displays the current channel value
        self._value_label: QtWidgets.QLabel = QtWidgets.QLabel(str(channel.value), self)

        # Button to set the channel to the max value 255
        self._max_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Max", self)

        # Slider to change the value and display the current value graphically
        self._slider: QtWidgets.QSlider = QtWidgets.QSlider(self)

        # Button to set the channel to the min value 0
        self._min_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Min", self)

        # Widget      Height
        # Address     30
        # Value       30
        # Max Button  30
        # Slider      256
        # Min Button  30

        self._channel.updated.connect(lambda x: self._update(x))

        self._address_label.setFixedSize(30, 20)
        self._address_label.move(0, 0)
        self._address_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._value_label.setFixedSize(30, 20)
        self._value_label.move(0, 20)
        self._value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self._max_button.setFixedSize(30, 20)
        self._max_button.move(0, 60)
        self._max_button.setStyleSheet(Style.BUTTON)
        self._max_button.clicked.connect(lambda: self._channel.update(255))

        self._slider.setMinimum(0)
        self._slider.setMaximum(255)
        self._slider.setFixedSize(30, 256)
        self._slider.move(0, 80)
        self._slider.setStyleSheet(Style.SLIDER)
        self._slider.valueChanged.connect(lambda x: self._channel.update(x))

        self._min_button.setFixedSize(30, 20)
        self._min_button.move(0, 336)
        self._min_button.setStyleSheet(Style.ACTIVE_BUTTON)
        self._min_button.clicked.connect(lambda: self._channel.update(0))

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
