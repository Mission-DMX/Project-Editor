"""Saving of UI hints and asset gathering."""
import json
import xml.etree.ElementTree as ET

from model import BoardConfiguration
from model.media_assets.media_type import MediaType
from model.media_assets.registry import get_all_assets_of_type


def _create_ui_hint_element(ui_hint: tuple[str, str], parent: ET.Element) -> ET.Element:
    """Creates an xml element of type uihint.

    <uihint name="key" value="value"/>
    """
    return ET.SubElement(parent, "uihint", attrib={
        "name": str(ui_hint[0]),
        "value": str(ui_hint[1]),
    })

def update_assets_ui_hint_element(board_configuration: BoardConfiguration) -> None:
    """Collect loaded asset information and update the corresponding UI hint."""
    assets_list = []
    for asset_type in [MediaType.IMAGE, MediaType.VIDEO, MediaType.AUDIO, MediaType.MODEL_3D, MediaType.TEXT]:
        assets_list.extend([{
                "uuid": str(asset.id),
                "type_hint": str(asset.get_factory_object_hint()),
                "name": str(asset.name),
                "data": str(asset.serialize_settings())
            } for asset in get_all_assets_of_type(asset_type)])
    board_configuration.ui_hints["media_assets"] = json.dumps(assets_list)
