import logging

import xml.etree.ElementTree as ET

from pyqtgraph.flowchart import Flowchart

import proto.UniverseControl_pb2 as proto
from model.board_configuration import BoardConfiguration, Scene, Filter, Universe


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
                _parse_uihint(child, board_configuration)
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
    for key, value in scene_element.attrib.items():
        match key:
            case "human_readable_name":
                human_readable_name = value
            case "id":
                id = int(value)
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing scene for show {board_configuration.show_name}")
    
    flowchart = Flowchart(name=human_readable_name)

    scene = Scene(id=id, human_readable_name=human_readable_name, flowchart=flowchart)

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
    pos = (0.0, 0.0)
    for key, value in filter_element.attrib.items():
        match key:
            case "id":
                id = value
            case "type":
                type = int(value)
            case "position":
                pos = tuple((float(s) for s in value.split(",")))
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing filter for scene {scene.human_readable_name}")

    filter = Filter(id, type, pos=pos)

    for child in filter_element:
        match child.tag:
            case "channellink":
                _parse_channellink(child, filter)
            case "initialParameters":
                _parse_inital_parameters(child, filter)
            case "filterConfiguration":
                _parse_filter_configuration(child, filter)
            case _:
                logging.warn(f"Filter {id} contains unknown element: {child.tag}")

    scene.filters.append(filter)


def _parse_channellink(initial_parameters_element: ET.Element, filter: Filter):
    cl_key = ""
    cl_value = ""
    for key, value in initial_parameters_element.attrib.items():
        match key:
            case "input_channel_id": 
                cl_key = value
            case "output_channel_id":
                cl_value = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing key-value-pair")
                
    filter.channel_links[cl_key] = cl_value


def _parse_inital_parameters(initial_parameters_element: ET.Element, filter: Filter):
    ip_key = ""
    ip_value = ""
    for key, value in initial_parameters_element.attrib.items():
        match key:
            case "name": 
                ip_key = value
            case "value":
                ip_value = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing initial paramter for filter {filter.id}")
                
    filter.initial_parameters[ip_key] = ip_value


def _parse_filter_configuration(filter_configuration_element: ET.Element, filter: Filter):
    fc_key = ""
    fc_value = ""
    for key, value in filter_configuration_element.attrib.items():
        match key:
            case "name": 
                fc_key = value
            case "value":
                fc_value = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing filter configuration for filter {filter.id}")
    
    if filter.type == 11 and fc_key != "universe":
        filter.filter_configurations[fc_value] = fc_key
        
    else:
        filter.filter_configurations[fc_key] = fc_value


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


    proto_universe = proto.Universe(id=id, physical_location=physical, remote_location=artnet, ftdi_dongle=ftdi)
    universe = Universe(universe_proto=proto_universe)
    universe.name = name
    universe.description = description

    board_configuration.universes.append(universe)


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
                logging.warn(f"Found attribute {key}={value} while parsing ftdi location")

    return proto.Universe.USBConfig(product_id=product_id, vendor_id=vendor_id, device_name=device_name, serial=serial_identifier)


def _parse_uihint(uihint_element: ET.Element, board_configuration: BoardConfiguration):
    uihint_key = ""
    uihint_value = ""
    for key, value in uihint_element.attrib.items():
        match key:
            case "name": 
                uihint_key = value
            case "value":
                uihint_value = value
            case _:
                logging.warn(f"Found attribute {key}={value} while parsing ui hint")

    board_configuration.ui_hints[uihint_key] = uihint_value