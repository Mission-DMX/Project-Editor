from abc import ABC, abstractmethod

from PySide6.QtWidgets import QWidget


class NodeEditorFilterConfigWidget(ABC):
    @abstractmethod
    def _get_configuration(self) -> dict[str, str]:
        raise NotImplementedError()

    @property
    def configuration(self) -> dict[str, str]:
        return self._get_configuration()

    @abstractmethod
    def get_widget(self) -> QWidget:
        raise NotImplementedError()
