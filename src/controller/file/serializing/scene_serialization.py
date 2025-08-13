"""Serialization of Scenes to XML."""
import xml.etree.ElementTree as ET

from controller.file.serializing.bankset_config_serialization import _create_scene_bankset
from controller.file.serializing.filter_serialization import (
    _create_filter_element_for_fish,
    create_channel_mappings_for_filter_set_for_fish,
)
from controller.file.serializing.fish_optimizer import SceneOptimizerModule
from controller.utils.process_notifications import ProcessNotifier
from model import Scene, UIPage
from model.scene import FilterPage


def _add_filter_page_to_element(scene_element: ET.Element, page: FilterPage,
                                parent_page: FilterPage | None) -> None:
    """Writes the filter pages of a scene or parent page.

    :param scene_element: The XML element to write to
    :param page: The filter page to serialize
    :param parent_page: This needs to be the parent page of the one to serialize (if any, otherwise pass None)
    """
    item = ET.SubElement(scene_element, "filterpage", attrib={
        "name": page.name,
        "parent": parent_page.name if parent_page else "",
    })
    for f in page.filters:
        filter_id_item = ET.SubElement(item, "filterid", attrib={})
        filter_id_item.text = f.filter_id
    for cp in page.child_pages:
        _add_filter_page_to_element(scene_element, cp, page)


def _add_ui_page_to_element(scene_element: ET.Element, ui_page: UIPage) -> None:
    """Add a UI page (the widgets one) to an existing scene element.

    :param scene_element: The parent scene XML element
    :param ui_page: The UI page to add
    """
    page_element = ET.SubElement(scene_element, "uipage", attrib={
        "title": str(ui_page.title),
    })
    from view.show_mode.show_ui_widgets import get_widget_key
    for widget in ui_page.widgets:
        widget_element = ET.SubElement(page_element, "widget", attrib={
            "posX": str(widget.position[0]),
            "posY": str(widget.position[1]),
            "sizeW": str(widget.size[0]),
            "sizeH": str(widget.size[1]),
            "filterID": ":".join(widget.filter_ids),
            "variante": str(get_widget_key(widget) or ""),
        })
        for k, v in widget.configuration.items():
            ET.SubElement(widget_element, "configurationEntry", attrib={
                "name": str(k),
                "value": str(v),
            })


def generate_scene_xml_description(assemble_for_fish_loading: bool, root: ET.Element, scene: Scene,
                                   pn: ProcessNotifier) -> None:
    """Generates the DOM tree for a given scene.

    :param assemble_for_fish_loading: Boolean that should be true if and only if the data is being transferred to fish
    :param root: The DOM root
    :param scene: The scene to generate the XML data for
    """
    scene_element = _create_scene_element(scene=scene, parent=root)
    if scene.linked_bankset and not assemble_for_fish_loading:
        _create_scene_bankset(root, scene)
    pn.total_step_count += len(scene.filters)
    om = SceneOptimizerModule(assemble_for_fish_loading)
    for filter_ in scene.filters:
        _create_filter_element_for_fish(filter_=filter_, parent=scene_element, for_fish=assemble_for_fish_loading,
                                        om=om)
        pn.current_step_number += 1
    create_channel_mappings_for_filter_set_for_fish(assemble_for_fish_loading, om, scene_element)
    if not assemble_for_fish_loading:
        for page in scene.pages:
            _add_filter_page_to_element(scene_element, page, None)

        for ui_page in scene.ui_pages:
            _add_ui_page_to_element(scene_element, ui_page)


def _create_scene_element(scene: Scene, parent: ET.Element) -> ET.Element:
    """Creates an XML element of a type scene.

    <scene human_readable_name="name" id="0">
      ...
    </scene>
    """
    se = ET.SubElement(parent, "scene", attrib={
        "id": str(scene.scene_id),
        "human_readable_name": str(scene.human_readable_name),
    })
    if scene.linked_bankset:
        se.attrib["linkedBankset"] = str(scene.linked_bankset.id)
    return se
