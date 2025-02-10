# coding=utf-8
from xml.etree import ElementTree

from controller.file.serializing.bankset_config_serialization import _create_scene_bankset
from controller.file.serializing.filter_serialization import (_create_filter_element_for_fish,
                                                              create_channel_mappings_for_filter_set_for_fish)
from controller.file.serializing.fish_optimizer import SceneOptimizerModule
from controller.utils.process_notifications import ProcessNotifier
from model import Scene, UIPage
from model.scene import FilterPage


def _add_filter_page_to_element(scene_element: ElementTree.Element, page: FilterPage, parent_page: FilterPage | None):
    item = ElementTree.SubElement(scene_element, "filterpage", attrib={
        'name': page.name,
        'parent': parent_page.name if parent_page else ''
    })
    for f in page.filters:
        filter_id_item = ElementTree.SubElement(item, "filterid", attrib={})
        filter_id_item.text = f.filter_id
    for cp in page.child_pages:
        _add_filter_page_to_element(scene_element, cp, page)


def _add_ui_page_to_element(scene_element: ElementTree.Element, ui_page: UIPage):
    page_element = ElementTree.SubElement(scene_element, "uipage", attrib={
        'title': ""
    })
    for widget in ui_page.widgets:
        widget_element = ElementTree.SubElement(page_element, "widget", attrib={
            'posX': str(widget.position[0]),
            'posY': str(widget.position[1]),
            'sizeW': str(widget.size[0]),
            'sizeH': str(widget.size[1]),
            'filterID': str(widget.filter_id),
            'variante': str(widget.get_variante())
        })
        for k, v in widget.configuration.items():
            config_element = ElementTree.SubElement(widget_element, "configurationEntry", attrib={
                'name': str(k),
                'value': str(v)
            })


def generate_scene_xml_description(assemble_for_fish_loading, root, scene, pn: ProcessNotifier):
    """
    This method generates the DOM tree for a given scene.

    :param assemble_for_fish_loading: Boolean that should be true if and only if the data is being transferred to fish
    :param root: The DOM root
    :param scene: The scene to generate the XML data for
    """
    scene_element = _create_scene_element(scene=scene, parent=root)
    if scene.linked_bankset and not assemble_for_fish_loading:
        _create_scene_bankset(root, scene_element, scene)
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


def _create_scene_element(scene: Scene, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type scene.

    <scene human_readable_name="name" id="0">
      ...
    </scene>
    """
    se = ElementTree.SubElement(parent, "scene", attrib={
        "id": str(scene.scene_id),
        "human_readable_name": str(scene.human_readable_name)
    })
    if scene.linked_bankset:
        se.attrib['linkedBankset'] = str(scene.linked_bankset.id)
    return se
