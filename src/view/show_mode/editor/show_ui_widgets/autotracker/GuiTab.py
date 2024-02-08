from abc import abstractmethod
from PySide6.QtWidgets import QWidget


class GuiTab(QWidget):
    """
    The `GuiTab` class represents a tab within a graphical user interface.

    Attributes:
        _id (int): An internal identifier for the tab.
        name (str): The name of the tab.
        instance: An shared instances safe.
        active (bool): Indicates whether the tab is currently active.

    Methods:
        - `__init__(name, instance)`: Initialize a GuiTab object with a name and instance.
        - `tab_changed(index)`: Callback when the active tab index changed.
        - `tab_activated()`: Called when the tab is activated.
        - `tab_deactivated()`: Called when the tab is deactivated.
        - `id`: Property for getting or setting the tab's internal identifier.
        - `video_update()`: Abstract method for updating video content within the tab.
    """

    def __init__(self, name, instance):
        """
        Initialize a GuiTab object.

        Args:
            name (str): The name of the tab.
            instance: An instance associated with the tab.
        """
        super().__init__()
        self._id = -1
        self.name = name
        self.instance = instance
        self.active = False

    def tab_changed(self, index):
        """
        Callback when the active tab is changed.

        Args:
            index (int): The new index of the tab.
        """
        if index == self.id:
            self.tab_activated()
        else:
            self.tab_deactivated()

    def tab_activated(self):
        """
        Called when the tab is activated.
        """
        self.active = True

    def tab_deactivated(self):
        """
        Called when the tab is deactivated.
        """
        self.active = False

    @property
    def id(self):
        """
        Get or set the tab's internal identifier.

        Returns:
            int: The internal identifier of the tab.
        """
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @abstractmethod
    def video_update(self):
        """
        Abstract method for updating video content within the tab.
        """
        pass
