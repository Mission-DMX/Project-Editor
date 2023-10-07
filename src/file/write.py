# coding=utf-8
"""Module to convert a board configuration to a xml element.

Usage:
    xml = createXML(board_configuration)
    writeDocument("ShowFiles/show_file.xml", xml)
"""
import logging
import os
from shutil import copyfile
from xml.etree import ElementTree

from model import Filter, Scene, Universe, BoardConfiguration, UIPage
from model.control_desk import BankSet, ColorDeskColumn, RawDeskColumn
from model.patching_channel import PatchingChannel
from model.scene import FilterPage
from proto import UniverseControl_pb2
from proto.Console_pb2 import lcd_color


def write_document(file_name: str, show_data: BoardConfiguration) -> bool:
    """Writes the xml element to the specified file.
    See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd for more information.
    
    Args:
        file_name: The (path and) file to which the xml element should be written.
        show_data: The show to save
        
    Returns: True, if successfully, otherwise false with error message.
    """
    xml = create_xml(show_data)
    copyfile(file_name, os.path.splitext(file_name)[0] + '.show_backup')
    with open(file_name, 'w+', encoding="UTF-8") as file:
        ElementTree.indent(xml)
        file.write(ElementTree.tostring(xml, encoding='unicode', method='xml'))
    return True
    # try:
    #
    #    return True
    # except IOError:
    #    print(f"Could not save {file_name}")
    #    return False


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


def lcd_color_to_string(display_color: lcd_color) -> str:
    match display_color:
        case lcd_color.white:
            return 'white'
        case lcd_color.red:
            return 'red'
        case lcd_color.blue:
            return 'blue'
        case lcd_color.cyan:
            return 'cyan'
        case lcd_color.black:
            return 'black'
        case lcd_color.green:
            return 'green'
        case lcd_color.magenta:
            return 'magenta'
        case lcd_color.yellow:
            return 'yellow'
        case _:
            return 'white'


def _create_scene_bankset(root_element: ElementTree.Element, scene_element: ElementTree.Element, scene: Scene):
    bs_element = ElementTree.SubElement(root_element, "bankset", attrib={
        'linked_by_default': "true",
        'id': str(scene.linked_bankset.id)
    })
    for bank in scene.linked_bankset.banks:
        bank_item = ElementTree.SubElement(bs_element, "bank")
        for col in bank.columns:
            if isinstance(col, ColorDeskColumn):
                column_item = ElementTree.SubElement(bank_item, "hslcolumn", attrib={
                    'color': col.color.format_for_filter()
                })
            elif isinstance(col, RawDeskColumn):
                column_item = ElementTree.SubElement(bank_item, "rawcolumn", attrib={
                    'secondary_text_line': col.secondary_text_line,
                    'fader_position': str(col.fader_position),
                    'encoder_position': str(col.encoder_position)
                })
            else:
                logging.error("Unsupported desk column type while saving file.")
                continue
            column_item.attrib['id'] = str(col.id)
            column_item.attrib['display_name'] = str(col.display_name)
            column_item.attrib['top_line_inverted'] = "true" if col.top_display_line_inverted else "false"
            column_item.attrib['bottom_line_inverted'] = "true" if col.bottom_display_line_inverted else "false"
            column_item.attrib['lcd_color'] = lcd_color_to_string(col.display_color)


def create_xml(board_configuration: BoardConfiguration) -> ElementTree.Element:
    """Creates a xml element from the given board configuration.
    
    Args:
        board_configuration: The board configuration to be converted.
    
    Returns:
        The xml element containing the board configuration.
        See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd for more information
    """
    root = _create_board_configuration_element(board_configuration)

    for scene in board_configuration.scenes:
        scene_element = _create_scene_element(scene=scene, parent=root)

        if scene.linked_bankset:
            _create_scene_bankset(root, scene_element, scene)

        for filter_ in scene.filters:

            filter_element = _create_filter_element(filter_=filter_, parent=scene_element)

            for channel_link in filter_.channel_links.items():
                _create_channel_link_element(channel_link=channel_link, parent=filter_element)

            for initial_parameter in filter_.initial_parameters.items():
                _create_initial_parameters_element(initial_parameter=initial_parameter, parent=filter_element)

            for filter_configuration in filter_.filter_configurations.items():
                _create_filter_configuration_element(filter_configuration=filter_configuration, parent=filter_element)

        for page in scene.pages:
            _add_filter_page_to_element(scene_element, page, None)

        for ui_page in scene.ui_pages:
            _add_ui_page_to_element(scene_element, ui_page)

    for universe in board_configuration.universes:
        universe_element = _create_universe_element(universe=universe, parent=root)

        proto = universe.universe_proto

        if proto.remote_location.ip_address != "":
            _create_artnet_location_element(artnet_location=proto.remote_location, parent=universe_element)
        elif proto.ftdi_dongle.vendor_id != "":
            _create_ftdi_location_element(ftdi_location=proto.ftdi_dongle, parent=universe_element)
        else:
            _create_physical_location_element(physical=proto.physical_location, parent=universe_element)

        _create_patching_element(patching=universe.patching, parent=universe_element)

    for device in board_configuration.devices:
        _create_device_element(device=device, parent=root)

    for ui_hint in board_configuration.ui_hints.items():
        _create_ui_hint_element(ui_hint=ui_hint, parent=root)

    return root


def _create_board_configuration_element(board_configuration: BoardConfiguration) -> ElementTree.Element:
    """Creates a xml element of type scene.
    
    <board_configuration xmlns:p1="http://www.asta.uni-luebeck.de/MissionDMX/ShowFile"
     default_active_scene="0" notes="notes" show_name="Show Name"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="ShowFile.xsd">
       ...
    </board_configuration>
    """
    # TODO we're not filling in the version attribute
    return ElementTree.Element("bord_configuration", attrib={
        "xmlns": "http://www.asta.uni-luebeck.de/MissionDMX/ShowFile",
        "xsi:schemaLocation": "http://www.asta.uni-luebeck.de/MissionDMX/ShowFile",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "show_name": str(board_configuration.show_name),
        "default_active_scene": str(board_configuration.default_active_scene),
        "notes": str(board_configuration.notes),
    })


def _create_scene_element(scene: Scene, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type scene.
    
    <scene human_readable_name="name" id="0">
      ...
    </scene>
    """
    se =  ElementTree.SubElement(parent, "scene", attrib={
        "id": str(scene.scene_id),
        "human_readable_name": str(scene.human_readable_name)
    })
    if scene.linked_bankset:
        se.attrib['linkedBankset'] = str(scene.linked_bankset.id)
    return se


def _create_filter_element(filter_: Filter, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type filter.
    
    <filter type="0" id="id">
      ...
    </filter>
    """
    return ElementTree.SubElement(parent, "filter", attrib={
        "id": str(filter_.filter_id),
        "type": str(filter_.filter_type),
        "pos": f"{filter_.pos[0]},{filter_.pos[1]}"
    })


def _create_channel_link_element(channel_link: tuple[str, str], parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type channellink.
    
    <channellink input_channel_id="id" output_channel_id="id">
    """

    # Some nodes have input and output named value.
    # Internally, the input is saved as 'value_in', but must be written as 'value'.
    return ElementTree.SubElement(parent, "channellink", attrib={
        "input_channel_id": "value" if channel_link[0] == "value_in" else str(channel_link[0]),
        "output_channel_id": str(channel_link[1])
    })


def _create_filter_configuration_element(filter_configuration: tuple[str, str],
                                         parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type filterConfiguration.
    
    <filterConfiguration name="key" value="value">
    """

    # if check for Universe node: Filter Configuration is saved backwards to display QLineEdit the right way
    key, value = filter_configuration
    return ElementTree.SubElement(parent, "filterConfiguration", attrib={
        "name": str(key) if "input_" not in key else str(value),
        "value": str(value) if "input_" not in key else str(key)
    })


def _create_initial_parameters_element(initial_parameter: tuple[str, str],
                                       parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type initialParameters.
    
    <initialParameters name="key" value="value">
    """
    return ElementTree.SubElement(parent, "initialParameters", attrib={
        "name": str(initial_parameter[0]),
        "value": str(initial_parameter[1])
    })


def _create_universe_element(universe: Universe, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type physical_location.

    <universe name="name" description="description" id="0">
        ...
    </universe>
    """
    return ElementTree.SubElement(parent, "universe", attrib={
        "id": str(universe.id),
        "name": str(universe.name),
        "description": str(universe.description)
    })


def _create_physical_location_element(physical: int, parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type physical_location.

    <physical_location>0</physical_location>
    """
    physical_location = ElementTree.SubElement(parent, "physical_location")
    physical_location.text = str(physical)
    return physical_location


def _create_artnet_location_element(artnet_location: UniverseControl_pb2.Universe.ArtNet,
                                    parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type artnet_location.
    
    <artnet_location ip_address="127.0.0.1" udp_port="666" device_universe_id="0" />
    """
    return ElementTree.SubElement(parent, "artnet_location", attrib={
        "ip_address": str(artnet_location.ip_address),
        "udp_port": str(artnet_location.port),
        "device_universe_id": str(artnet_location.universe_on_device)
    })


def _create_ftdi_location_element(ftdi_location: UniverseControl_pb2.Universe.USBConfig,
                                  parent: ElementTree.Element) -> ElementTree.Element:
    """Creates a xml element of type ftdi_location.
    
    <ftdi_location vendor_id="0" product_id="0" device_name="name"/>
    """
    # vendor_id=0x0403, product_id=0x6001
    return ElementTree.SubElement(parent, "ftdi_location", attrib={
        "vendor_id": str(ftdi_location.vendor_id),
        "product_id": str(ftdi_location.product_id),
        "device_name": str(ftdi_location.device_name),
        "serial_identifier": str(ftdi_location.serial)
    })


def _create_patching_element(patching: list[PatchingChannel], parent: ElementTree.Element):
    patching_element = ElementTree.SubElement(parent, "patching")
    index: int = 0
    while index < len(patching):
        channel = patching[index]
        if not channel.fixture.name == "Empty":
            ElementTree.SubElement(patching_element, "fixture", attrib={
                "start": str(channel.address),
                "fixture_file": channel.fixture.fixture_file,
                "mode": str(channel.fixture.mode_index)
            })
            index += len(channel.fixture.mode["channels"])
        else:
            index += 1


def _create_device_element(device, parent: ElementTree.Element) -> ElementTree.Element:
    """TODO implement
    
    <device channel="0" name="name" type="type" universe_id="0">
    """


def _create_ui_hint_element(ui_hint: tuple[str, str], parent: ElementTree.Element) -> ElementTree.Element:
    """Creates an xml element of type uihint.
    
    <uihint name="key" value="value"/>
    """
    return ElementTree.SubElement(parent, "uihint", attrib={
        "name": str(ui_hint[0]),
        "value": str(ui_hint[1])
    })
