"""Module provides abstract filter node configuration widget."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from view.show_mode.editor.nodes import FilterNode


class NodeEditorFilterConfigWidget(ABC):
    """Base class for node editor filter configuration widgets.

    All abstract methods must be implemented. They need to return a non-null value at all times. Dictionaries however,
    might be returned empty if no changes should be made.

    """

    @abstractmethod
    def _get_configuration(self) -> dict[str, str]:
        """Retrieve the filter configuration parameters that should be updated."""

    @abstractmethod
    def _load_configuration(self, conf: dict[str, str]) -> None:
        pass

    @property
    def configuration(self) -> dict[str, str]:
        """Returns the configuration of the filter."""
        return self._get_configuration()

    @configuration.setter
    def configuration(self, conf: dict[str, str]) -> None:
        """Loads the configuration already present in the filter configuration."""
        self._load_configuration(conf)

    @abstractmethod
    def get_widget(self) -> QWidget:
        """Returns the widget that should be displayed."""

    @abstractmethod
    def _load_parameters(self, parameters: dict[str, str]) -> dict:
        """Parse the current filter parameters."""

    @abstractmethod
    def _get_parameters(self) -> dict[str, str]:
        """Return the (initial) filter parameters deduced by the widget.

        Only parameters that changed need to be updated here.

        """
        raise NotImplementedError

    @property
    def parameters(self) -> dict[str, str]:
        """Returns the current filter parameters."""
        return self._get_parameters()

    @parameters.setter
    def parameters(self, parameters: dict[str, str]) -> None:
        """Sets the filter parameters on the widget."""
        self._load_parameters(parameters)

    def parent_closed(self, filter_node: "FilterNode") -> None:
        """This method might be overridden to listen for parent close events.

        Args:
            filter_node -- might be used to alter the filter being presented.

        """
        filter_node.update_node_after_settings_changed()
        if filter_node.fsi is not None:
            filter_node.fsi.update_position()

    @abstractmethod
    def parent_opened(self) -> None:
        """This method might be overridden to listen for parent open events."""
