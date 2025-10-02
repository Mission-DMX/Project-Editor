"""Module contains methods to construct assets based on their descriptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.media_assets.factory_hint import AssetFactoryObjectHint
from model.media_assets.image import LocalImage

if TYPE_CHECKING:
    from model.media_assets.asset import MediaAsset

def load_asset(uuid: str, type_hint: AssetFactoryObjectHint | str, serialized_data: str, show_file_path: str = "",
               name: str = "") -> MediaAsset | None:
    """Load a media asset based on type and provided data.

    Args:
        uuid: The uuid of the media asset
        type_hint: The type of the asset
        serialized_data: The serialized data of the asset
        show_file_path: The file path of the asset. Default: empty string if no show file path is available
        name: The name of the asset if any.

    Returns:
        MediaAsset | None: The media asset if it was loadable.

    """
    if isinstance(type_hint, str):
        type_hint = AssetFactoryObjectHint(type_hint)
    asset: MediaAsset | None = None
    match type_hint:
        case AssetFactoryObjectHint.IMAGE_EXTERNAL_FILE:
            asset = LocalImage(serialized_data, uuid, show_file_path)
        case _:
            asset = None
    if asset is not None:
        asset.name = name
    return asset
