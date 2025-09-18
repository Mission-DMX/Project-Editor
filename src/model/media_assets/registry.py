"""File contains the media registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from model.media_assets.media_type import MediaType

if TYPE_CHECKING:
    from model.media_assets.asset import MediaAsset

_asset_library: dict[MediaType, dict[str, MediaAsset]] = {}

def register(asset: MediaAsset, uuid: str) -> bool:
    """Method registers a media asset.

    Args:
        asset (MediaAsset): the media asset to register
        uuid (str): the uuid of the media asset

    Returns:
        bool: True if registration was successful, False if an Asset with that UUID was already registered.

    """
    if get_asset_by_uuid(uuid) is not None:
        return False
    d = _asset_library.get(asset.get_type())
    if d is None:
        d = {}
        _asset_library[asset.get_type()] = d
    d[uuid] = asset
    return True

def get_asset_by_uuid(uuid: str) -> MediaAsset | None:
    """Get a media asset by its UUID.

    Args:
        uuid (str): the uuid of the media asset

    Returns:
        MediaAsset: the media asset or None if it could not be found.

    """
    for lib in _asset_library.values():
        if uuid in lib:
            return lib[uuid]
    return None

def get_all_assets_of_type(asset_type: MediaType) -> list[MediaAsset]:
    """Get all media assets of type asset_type."""
    if asset_type not in _asset_library:
        return []
    return list(_asset_library[asset_type].values())

def clear() -> None:
    """Clear all media assets."""
    _asset_library.clear()
