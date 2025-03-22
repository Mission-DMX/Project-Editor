# coding=utf-8
from PySide6.QtWidgets import QGridLayout, QLabel, QLayout, QLineEdit, QPushButton

from controller.autotrack.Helpers.InstanceManager import InstanceManager
from view.show_mode.show_ui_widgets.autotracker.GuiTab import GuiTab


class SettingsTab(GuiTab):
    """
    The `SettingsTab` class represents a tab for configuring application settings.

    Attributes:
        name (str): The name of the tab.
        instance (InstanceManager): An instance manager for managing application instances and settings.

    Methods:
        - `__init__(name, instance)`: Initialize a SettingsTab object with a name and an instance manager.
        - `save_settings()`: Save the settings entered in the QLineEdit widgets.
        - `tab_activated()`: Called when the tab is activated.
        - `video_update()`: Abstract method for updating video content within the tab.
    """

    def __init__(self, name, instance: InstanceManager):
        """
        Initialize a SettingsTab object.

        Args:
            name (str): The name of the tab.
            instance (InstanceManager): An instance manager for managing application instances and settings.
        """
        if isinstance(instance, InstanceManager):
            super().__init__(name, instance)
            settings = self.instance.settings.settings
        else:
            super().__init__(name, None)
            settings = instance

        layout = QGridLayout()
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        layout.addWidget(QLabel("Crop:"), 0, 0)
        self.crop_line_edit = QLineEdit()
        layout.addWidget(self.crop_line_edit, 0, 1)
        self.crop_line_edit.setEnabled(self.instance is not None)

        for setting, value in settings.items():
            label = QLabel(setting)
            edit = QLineEdit()
            edit.setText(value)
            layout.addWidget(label)
            layout.addWidget(edit)
            settings[setting] = edit

        self.setLayout(layout)

        if isinstance(instance, InstanceManager):
            save_button = QPushButton("Save")
            layout.addWidget(save_button)
            save_button.clicked.connect(self.save_settings)

    def save_settings(self):
        """
        Save the settings entered in the QLineEdit widgets.
        """
        filter_config = self.instance.filter.filter_configurations
        for setting, edit in self.instance.settings.settings.items():
            value = edit.text()
            filter_config[setting] = value

    def tab_activated(self):
        """
        Called when the tab is activated.
        """
        if self.instance:
            self.crop_line_edit.setText(", ".join(map(str, self.instance.settings.crop)))

    def video_update(self):
        """
        Abstract method for updating video content within the tab.
        """
        pass
