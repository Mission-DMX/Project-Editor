from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget


class NodeEditorFilterConfigWidget(ABC):
    @abstractmethod
    def _get_configuration(self) -> dict[str, str]:
        raise NotImplementedError()

    @abstractmethod
    def _load_configuration(self, conf: dict[str, str]):
        raise NotImplementedError

    @property
    def configuration(self) -> dict[str, str]:
        """Returns the configuration of the filter"""
        return self._get_configuration()

    @configuration.setter
    def configuration(self, conf: dict[str, str]):
        """Loads the configuration already present in the filter configuration"""
        self._load_configuration(conf)

    @abstractmethod
    def get_widget(self) -> QWidget:
        """Returns the widget that should be displayed"""
        raise NotImplementedError()
