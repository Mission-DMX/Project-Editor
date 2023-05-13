import logging

import xml.etree.ElementTree as ET

from pyqtgraph.flowchart import Flowchart

import proto.UniverseControl_pb2 as proto
from DMXModel import BoardConfiguration, Scene, Filter


def readDocument(file_name: str) -> BoardConfiguration:
    board_configuration = BoardConfiguration()

    tree = ET.parse(file_name)
    root = tree.getroot()

    prefix = ""

    for key, value in root.attrib.items():
        match key:
            case "show_name":
                board_configuration.show_name = value
            case  "default_active_scene":
                board_configuration.default_active_scene = value
            case "notes":
                board_configuration.notes = value
            case "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                prefix = "{" + value + "}"
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing board configuration")

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
                _parse_key_value_pair(child, "name", "value", board_configuration.ui_hints)
            case _:
                logging.warn(f"Show {board_configuration.show_name} contains unknown element: {child.tag}")


    return board_configuration


def _clean_tags(element: ET.Element, prefix: str):
    for child in element:
        child.tag = child.tag.replace(prefix, '')
        _clean_tags(child, prefix)


def _parse_scene(scene_element: ET.Element, board_configuration: BoardConfiguration):
    human_readable_name = ""
    id = 0
    filters: list[Filter] = []
    for key, value in scene_element.attrib.items():
        match key:
            case "human_readable_name":
                human_readable_name = value
            case "id":
                id = int(value)
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing scene for show {board_configuration.show_name}")
    
    flowchart = Flowchart(name=human_readable_name)

    scene = Scene(id=id, human_readable_name=human_readable_name, flowchart=flowchart, filters=[])

    for child in scene_element:
        match child.tag:
            case "filter":
                _parse_filter(child, scene)
            case _:
                logging.warn(f"Scene {human_readable_name} contains unknown element: {child.tag}")

    board_configuration.scenes.append(scene)


def _parse_filter(filter_element: ET.Element, scene: Scene):
    id = ""
    type = 0
    for key, value in filter_element.attrib.items():
        match key:
            case "id":
                id = value
            case "type":
                type = int(value)
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing filter for scene {scene.human_readable_name}")

    filter = Filter(id, type)

    for child in filter_element:
        match child.tag:
            case "channellink":
                _parse_key_value_pair(child, "input_channel_id", "output_channel_id", filter.channel_links)
            case "initialParameters":
                _parse_key_value_pair(child, "name", "value", filter.initial_parameters)
            case "filterConfiguration":
                _parse_key_value_pair(child, "name", "value", filter.filter_configurations)
            case _:
                logging.warn(f"Filter {id} contains unknown element: {child.tag}")

    scene.filters.append(filter)


def _parse_device(device_element: ET.Element, board_configuration: BoardConfiguration):
    """TODO Implement"""
    pass


def _parse_universe(universe_element: ET.Element, board_configuration: BoardConfiguration):
    id = None
    name = ""
    description = ""
    for key, value in universe_element.attrib.items():
        match key:
            case "id":
                id = int(value)
            case "name":
                name = value
            case "description":
                description = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing universe for show {board_configuration.show_name}")

    if id is None:
        logging.error(f"Could not parse universe element, id attribute is missing")

    physical: int = None
    artnet: proto.Universe.ArtNet = None
    ftdi: proto.Universe.ArtNet = None

    for child in universe_element:
        match child.tag:
            case "physical_location":
                physical = _parse_physical_location(child)
            case "artnet_location":
                artnet = _parse_artnet_location(child)
            case "ftdi_location":
                ftdi = _parse_ftdi_location(child)
            case _:
                logging.warn(f"Universe {id} contains unknown element: {child.tag}")

    if physical is None and artnet is None and ftdi is None:
        logging.warn(f"Could not parse any location for universe {id}")

    universe = proto.Universe(id=id, physical_location=physical, remote_location=artnet, ftdi_dongle=ftdi)

    board_configuration.universes.append(filter)


def _parse_physical_location(location_element: ET.Element) -> int:
    return int(location_element.text)


def _parse_artnet_location(location_element: ET.Element) -> proto.Universe.ArtNet:
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
                logging.warn(f"Found attribute {key}={value} while parsing artnet location")

    return proto.Universe.ArtNet(ip_address=ip_address, port=udp_port, universe_on_device=device_universe_id)


def _parse_ftdi_location(location_element: ET.Element) -> proto.Universe.USBConfig:
    product_id = 0
    vendor_id = 0
    device_name = ""
    serial = ""
    for key, value in location_element.attrib.items():
        match key:
            case "product_id":
                product_id = int(value)
            case "vendor_id":
                vendor_id = int(value)
            case "device_name":
                device_name = value
            case "serial":
                serial = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing ftdi location")

    return proto.Universe.USBConfig(product_id=product_id, vendor_id=vendor_id, device_name=device_name, serial=serial)


def _parse_key_value_pair(key_value_pair_element: ET.Element, key_name: str, value_name: str, map: dict[str, str]):
    pair_key = ""
    pair_value = ""
    for key, value in key_value_pair_element:
        match key:
            case str(key_name):
                pair_key = value
            case str(value_name):
                pair_value = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing key-value-pair")

    map[pair_key] = pair_value