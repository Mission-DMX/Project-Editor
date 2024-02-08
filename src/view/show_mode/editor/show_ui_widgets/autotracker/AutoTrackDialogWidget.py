from PySide6.QtCore import QTimer, QThread
from PySide6.QtWidgets import QMainWindow, QMenuBar, QTabWidget, QWidget

from model.virtual_filters import AutoTrackerFilter
from view.show_mode.editor.show_ui_widgets.autotracker.GuiTab import GuiTab
from view.show_mode.editor.show_ui_widgets.autotracker.SourcesTab import SourcesTab
from view.show_mode.editor.show_ui_widgets.autotracker.SettingsTab import SettingsTab
from view.show_mode.editor.show_ui_widgets.autotracker.CropTab import CropTab
from controller.autotrack.Helpers.InstanceManager import InstanceManager
#from view.show_mode.editor.show_ui_widgets.autotracker.DetectionTab import DetectionTab
from view.show_mode.editor.show_ui_widgets.autotracker.LightSetupTab import LightSetupTab


class AutoTrackDialogWidget(QTabWidget):
    """
    The `MainWindow` class represents the main application window.

    Attributes:
        instance (InstanceManager): An instance manager for managing application instances and settings.
        tab_widget (QTabWidget): The widget that holds the application tabs.

    Methods:
        - `__init__()`: Initialize the main application window.
        - `video_update_all()`: Update video content for all active tabs.
        - `tab_changed(index)`: Handle tab change events.
        - `register_tabs(tab_widget, tabs)`: Register tabs in the main window.
    """

    def __init__(self, f: AutoTrackerFilter):
        """
        Initialize the main application window.
        """
        super().__init__()
        self.instance = InstanceManager(f)
        tabs = [
            SourcesTab("Sources", self.instance),
            SettingsTab("Settings", self.instance),
            CropTab("Crop", self.instance),
            #DetectionTab("Detect", self.instance),
            LightSetupTab("Lights", self.instance),
        ]
        self.register_tabs(self, tabs)

        # Set the tab widget as the central widget

        self.currentChanged.connect(self.tab_changed)

        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.video_update_all)
        self.video_timer.start(1)

    def video_update_all(self):
        """
        Update video content for all active tabs.
        """
        for i in range(self.count()):
            tab = self.widget(i)
            if isinstance(tab, GuiTab):
                tab.video_update()

    def tab_changed(self, index):
        """
        Handle tab change events.

        Args:
            index (int): The index of the selected tab.
        """
        for i in range(self.count()):
            tab = self.widget(i)
            if isinstance(tab, GuiTab):
                tab.tab_changed(index)

    def register_tabs(self, tab_widget, tabs):
        """
        Register tabs in the main window.

        Args:
            tab_widget (QTabWidget): The tab widget to register tabs in.
            tabs (list): A list of tab objects to register.
        """
        first = True
        for tab in tabs:
            tab_widget.addTab(tab, tab.name)
            tab.id = tab_widget.count() - 1
            if first:
                tab.tab_activated()
                first = False
