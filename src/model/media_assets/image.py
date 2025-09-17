from abc import ABC, abstractmethod
from typing import override

from PySide6.QtGui import QImage

from model.media_assets.asset import MediaAsset
from model.media_assets.media_type import MediaType


class AbstractImageAsset(MediaAsset, ABC):
    """An abstract Image."""

    def __init__(self, uuid: str) -> None:
        super().__init__(uuid)

    @override
    def get_type(self) -> MediaType:
        return MediaType.IMAGE

    @abstractmethod
    def get_image_for_ui(self) -> QImage:
        """This method must return a QImage to be used inside the editor.

        Returns:
            QImage: The image to be used by the UI.
        """
        raise NotImplementedError
