from abc import ABC, abstractmethod


class NodeEditorWidget(ABC):
    @abstractmethod
    def _get_configuration(self) -> dict[str, str]:
        raise NotImplementedError()

    @property
    def configuration(self) -> dict[str, str]:
        return self._get_configuration()
