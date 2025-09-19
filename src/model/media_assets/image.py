"""Module contains image asset implementations."""

import os
from abc import ABC, abstractmethod
from logging import getLogger
from typing import override

from PySide6.QtGui import QImage, QPixmap, Qt

from model.media_assets.asset import GLOBAL_ASSET_FOLDER, MediaAsset
from model.media_assets.factory_hint import AssetFactoryObjectHint
from model.media_assets.media_type import MediaType
from utility import resource_path

logger = getLogger(__name__)
_NO_IMAGE_FOUND_PLACEHOLDER = QImage(resource_path(os.path.join("resources", "icons", "assets_no_image.png")))


class AbstractImageAsset(MediaAsset, ABC):
    """An abstract Image."""

    def __init__(self, uuid: str) -> None:
        """Constructor only calls super constructor."""
        super().__init__(uuid)

    @override
    def get_type(self) -> MediaType:
        return MediaType.IMAGE

    @abstractmethod
    def get_image_for_ui(self) -> QImage:
        """Method must return a QImage to be used inside the editor.

        Returns:
            The image to be used by the UI.

        """
        raise NotImplementedError

class LocalImage(AbstractImageAsset):
    """An image located in a local file."""

    def __init__(self, path: str, uuid: str = "", show_file_path: str = "") -> None:
        """Load and register an image located in a local file.

        Args:
            path: The path to the local file.
            uuid: The UUID of the asset.
            show_file_path: The path to the current show file. Leave as empty string if none is loaded.

        """
        super().__init__(uuid)
        self._path = path
        if not os.path.isfile(path):
            global_asset_dir = os.path.join(GLOBAL_ASSET_FOLDER, "images")
            if not os.path.exists(global_asset_dir):
                os.mkdir(global_asset_dir)
            if os.path.isfile(os.path.join(global_asset_dir, path)):
                path = os.path.join(global_asset_dir, path)
            elif len(show_file_path) > 0:
                potential_file_path = os.path.join(os.path.dirname(os.path.abspath(show_file_path)), path)
                if os.path.isfile(potential_file_path):
                    path = potential_file_path
            else:
                path = None
                logger.error("Could not find asset of type image based on path '%s'. "
                             "Searched global asset directory: %s", path, global_asset_dir)
        if path is not None:
            self._image: QImage = QImage(path)
        else:
            self._image: QImage = _NO_IMAGE_FOUND_PLACEHOLDER
        resized_image = self._image.scaled(
            64, 64,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self._thumbnail = QPixmap.fromImage(resized_image)

    @override
    def get_image_for_ui(self) -> QImage:
        return self._image

    @override
    def get_thumbnail(self) -> QPixmap:
        return self._thumbnail

    @override
    def serialize_settings(self) -> str:
        return self._path

    @override
    def get_factory_object_hint(self) -> AssetFactoryObjectHint:
        return AssetFactoryObjectHint.IMAGE_EXTERNAL_FILE
