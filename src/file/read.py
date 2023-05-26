# coding=utf-8
"""Handles reading a xml document"""
import logging
from xml.etree import ElementTree

from pyqtgraph.flowchart import Flowchart

import proto.UniverseControl_pb2 as Proto
from model import BoardConfiguration, Scene, Universe, Filter
from model.patching_universe import PatchingUniverse
from view.show_mode.library import FilterNodeLibrary


def read_document(file_name: str, board_configuration: BoardConfiguration):
    """Parses the specified file to a board configuration data model.
    
    Args:
        file_name: The path to the file to be parsed.
        
    Returns:
        A BoardConfiguration instance parsed from the provided file.
    """
    board_configuration.broadcaster.clear_board_configuration.emit()
    tree = ElementTree.parse(file_name)
    root = tree.getroot()

    prefix = ""

    for key, value in root.attrib.items():
        match key:
            case "show_name":
                board_configuration.show_name = value
            case "default_active_scene":
                board_configuration.default_active_scene = value
            case "notes":
                board_configuration.notes = value
            case "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                prefix = "{" + value + "}"
            case _:
                logging.warning("Found attribute %s=%s while parsing board configuration", key, value)

    _clean_tags(root, prefix)

    for child in root:
        match child.tag:
            case "scene":
                _parse_scene(child, board_configuration)
            case "device":
                _parse_device(child, board_configuration)
            case "universe":
                _parse_universe(child, board_configuration)
            case "uihint":
                _parse_ui_hint(child, board_configuration)
            case _:
                logging.warning("Show %s contains unknown element: %s",
                                board_configuration.show_name, child.tag)

    board_configuration.broadcaster.board_configuration_loaded.emit()


def _clean_tags(element: ElementTree.Element, prefix: str):
    for child in element:
        child.tag = child.tag.replace(prefix, '')
        _clean_tags(child, prefix)


def _parse_scene(scene_element: ElementTree.Element, board_configuration: BoardConfiguration):
    human_readable_name = ""
    scene_id = 0
    for key, value in scene_element.attrib.items():
        match key:
            case "human_readable_name":
                human_readable_name = value
            case "id":
                scene_id = int(value)
            case _:
                logging.warning(
                    "Found attribute %s=%s while parsing scene for show %s",
                    key, value, board_configuration.show_name)

    flowchart = Flowchart(name=human_readable_name, library=FilterNodeLibrary())

    scene = Scene(scene_id=scene_id,
                  human_readable_name=human_readable_name,
                  flowchart=flowchart,
                  board_configuration=board_configuration)

    for child in scene_element:
        match child.tag:
            case "filter":
                _parse_filter(child, scene)
            case _:
                logging.warning("Scene %s contains unknown element: %s",
                                human_readable_name, child.tag)

    board_configuration.broadcaster.scene_created.emit(scene)


def _parse_filter(filter_element: ElementTree.Element, scene: Scene):
    filter_id = ""
    filter_type = 0
    pos = (0.0, 0.0)
    for key, value in filter_element.attrib.items():
        match key:
            case "id":
                filter_id = value
            case "type":
                filter_type = int(value)
            case "pos":
                pos = tuple((float(s) for s in value.split(",")))
            case _:
                logging.warning(
                    "Found attribute %s=%s while parsing filter for scene %s",
                    key, value, scene.human_readable_name)

    filter_ = Filter(scene=scene, filter_id=filter_id, filter_type=filter_type, pos=pos)

    for child in filter_element:
        match child.tag:
            case "channellink":
                _parse_channel_link(child, filter_)
            case "initialParameters":
                _parse_initial_parameters(child, filter_)
            case "filterConfiguration":
                _parse_filter_configuration(child, filter_)
            case _:
                logging.warning("Filter %s contains unknown element: %s", filter_id, child.tag)

    scene.filters.append(filter_)


def _parse_channel_link(initial_parameters_element: ElementTree.Element, filter_: Filter):
    cl_key = ""
    cl_value = ""
    for key, value in initial_parameters_element.attrib.items():
        match key:
            case "input_channel_id":
                cl_key = value
            case "output_channel_id":
                cl_value = value
            case _:
                logging.warning("Found attribute %s=%s while parsing key-value-pair", key, value)

    filter_.channel_links[cl_key] = cl_value


def _parse_initial_parameters(initial_parameters_element: ElementTree.Element, filter_: Filter):
    ip_key = ""
    ip_value = ""
    for key, value in initial_parameters_element.attrib.items():
        match key:
            case "name":
                ip_key = value
            case "value":
                ip_value = value
            case _:
                logging.warning("Found attribute %s=%s while parsing initial parameter for filter %s",
                                key, value, filter_.filter_id)

    filter_.initial_parameters[ip_key] = ip_value


def _parse_filter_configuration(filter_configuration_element: ElementTree.Element, filter_: Filter):
    fc_key = ""
    fc_value = ""
    for key, value in filter_configuration_element.attrib.items():
        match key:
            case "name":
                fc_key = value
            case "value":
                fc_value = value
            case _:
                logging.warning("Found attribute %s=%s while parsing filter configuration for filter %s",
                                key, value, filter_.filter_id)

    if filter_.filter_type == 11 and fc_key != "universe":
        filter_.filter_configurations[fc_value] = fc_key
    else:
        filter_.filter_configurations[fc_key] = fc_value


def _parse_device(device_element: ElementTree.Element, board_configuration: BoardConfiguration):
    """TODO Implement"""


def _parse_universe(universe_element: ElementTree.Element, board_configuration: BoardConfiguration):
    universe_id = None
    name = ""
    description = ""
    for key, value in universe_element.attrib.items():
        match key:
            case "id":
                universe_id = int(value)
            case "name":
                name = value
            case "description":
                description = value
            case _:
                logging.warning("Found attribute %s=%s while parsing universe for show %s",
                                key, value, board_configuration.show_name)

    if universe_id is None:
        logging.error("Could not parse universe element, id attribute is missing")

    physical: int | None = None
    artnet: Proto.Universe.ArtNet | None = None
    ftdi: Proto.Universe.ArtNet | None = None

    for child in universe_element:
        match child.tag:
            case "physical_location":
                physical = _parse_physical_location(child)
            case "artnet_location":
                artnet = _parse_artnet_location(child)
            case "ftdi_location":
                ftdi = _parse_ftdi_location(child)
            case _:
                logging.warning("Universe %s contains unknown element: %s",
                                universe_id, child.tag)

    if physical is None and artnet is None and ftdi is None:
        logging.warning("Could not parse any location for universe %s", universe_id)

    universe_proto = Proto.Universe(id=universe_id,
                                    physical_location=physical,
                                    remote_location=artnet,
                                    ftdi_dongle=ftdi)
    patching_universe = PatchingUniverse(universe_proto)
    universe = Universe(patching_universe)
    universe.name = name
    universe.description = description

    board_configuration.broadcaster.add_universe.emit(patching_universe)


def _parse_physical_location(location_element: ElementTree.Element) -> int:
    return int(location_element.text)


def _parse_artnet_location(location_element: ElementTree.Element) -> Proto.Universe.ArtNet:
    device_universe_id = 0
    ip_address = ""
    udp_port = 0
    for key, value in location_element.attrib.items():
        match key:
            case "device_universe_id":
                device_universe_id = int(value)
            case "ip_address":
                ip_address = value
            case "udp_port":
                udp_port = int(value)
            case _:
                logging.warning("Found attribute %s=%s while parsing artnet location", key, value)

    return Proto.Universe.ArtNet(ip_address=ip_address, port=udp_port, universe_on_device=device_universe_id)


def _parse_ftdi_location(location_element: ElementTree.Element) -> Proto.Universe.USBConfig:
    product_id = 0
    vendor_id = 0
    device_name = ""
    serial_identifier = ""
    for key, value in location_element.attrib.items():
        match key:
            case "product_id":
                product_id = int(value)
            case "vendor_id":
                vendor_id = int(value)
            case "device_name":
                device_name = value
            case "serial_identifier":
                serial_identifier = value
            case _:
                logging.warning("Found attribute %s=%s while parsing ftdi location", key, value)

    return Proto.Universe.USBConfig(product_id=product_id,
                                    vendor_id=vendor_id,
                                    device_name=device_name,
                                    serial=serial_identifier)


def _parse_ui_hint(ui_hint_element: ElementTree.Element, board_configuration: BoardConfiguration):
    ui_hint_key = ""
    ui_hint_value = ""
    for key, value in ui_hint_element.attrib.items():
        match key:
            case "name":
                ui_hint_key = value
            case "value":
                ui_hint_value = value
            case _:
                logging.warning("Found attribute %s=%s while parsing ui hint", key, value)

    board_configuration.ui_hints[ui_hint_key] = ui_hint_value