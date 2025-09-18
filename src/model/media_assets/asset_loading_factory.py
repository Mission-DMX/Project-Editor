"""Module contains methods to construct assets based on their descriptions"""
from typing import TYPE_CHECKING

from model.media_assets.factory_hint import AssetFactoryObjectHint
from model.media_assets.image import LocalImage

if TYPE_CHECKING:
    from model.media_assets.asset import MediaAsset

def load_asset(uuid: str, type_hint: AssetFactoryObjectHint, serialized_data: str, show_file_path: str = "")\
        -> "MediaAsset | None":
    """Load a media asset based on type and provided data.

    Args:
        uuid (str): The uuid of the media asset
        type_hint (AssetFactoryObjectHint): The type of the asset
        serialized_data (str): The serialized data of the asset
        show_file_path (str): The file path of the asset. Default: empty string if no show file path is available

    Returns:
        MediaAsset | None: The media asset if it was loadable.

    """
    match type_hint:
        case AssetFactoryObjectHint.IMAGE_EXTERNAL_FILE:
            return LocalImage(serialized_data, uuid, show_file_path)
        case _:
            return None
