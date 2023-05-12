"""Module to convert a board configuration to an xml element.

Usage:
    xml = createXML(board_configuration)
    writeDocument("ShowFiles/show_file.xml", xml)
"""
import xml.etree.ElementTree as ET

import proto.UniverseControl_pb2 as proto
from DMXModel import BoardConfiguration, Scene, Filter
from model.universe import Universe
from widgets.NodeEditor.Nodes import FilterNode


def writeDocument(file_name: str, xml: ET.Element) -> bool:
    """Writes the xml element to the specified file.
    See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd for more information.
    
    Args:
        file_name: The (path and) file to which the xml element should be written.
        xml: The xml element to write
        
    Returns: True, if successfull, otherwise false with error message.
    """
    tree = ET.ElementTree(xml)
    try:
        tree.write(file_name)
        return True
    except IOError:
        print(f"Could not save {file_name}")
        return False


def createXML(board_configuration: BoardConfiguration) -> ET.Element:
    """Creates an xml element from the given board configuration.
    
    Args:
        board_configuration: The board configuration to be converted.
    
    Returns:
        The xml element containing the board configuration.
        See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd for more information.
    """
    root = _create_board_configuration_element(board_configuration)

    for scene in board_configuration.scenes:
        scene_element = _create_scene_element(scene=scene, parent=root)

        for _, node in scene.flowchart.nodes().items():
            if not isinstance(node, FilterNode):
                return False

            filter_element = _create_filter_element(filter=node.filter, parent=scene_element)

            for channel_link in node.filter.channel_links.items():
                _create_channel_link_element(channel_link=channel_link, parent=filter_element)

            for initial_parameter in node.filter.initial_parameters.items():
                _create_inital_parameters_element(initial_parameter=initial_parameter, parent=filter_element)

            for filter_configuration in node.filter.filter_configurations.items():
                _create_filter_configuration_element(filter_configuration=filter_configuration, parent=filter_element)

    for universe in board_configuration.universes:
        universe_element = _create_universe_element(universe=universe, parent=root)

        # TODO Universe location

    for device in board_configuration.devices:
        _create_device_element(device=device, parent=root)

    for uihint in board_configuration.ui_hints:
        _create_uihint_element(uihint=uihint, parent=root)

    return root


def _create_board_configuration_element(board_configuration: BoardConfiguration) -> ET.Element:
    """Creates an xml element of type scene.
    
    <board_configuration xmlns:p1="http://www.asta.uni-luebeck.de/MissionDMX/ShowFile" default_active_scene="0" notes="notes" show_name="Show Name" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="ShowFile.xsd">
       ...
    </board_configuration>
    """
    return ET.Element("bord_configuration", attrib={
        "xmlns": "http://www.asta.uni-luebeck.de/MissionDMX/ShowFile",
        "xsi:schemaLocation": "http://www.asta.uni-luebeck.de/MissionDMX/ShowFile",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "show_name": board_configuration.show_name,
        "default_active_scene": str(board_configuration.default_active_scene),
        "notes": board_configuration.notes
    })


def _create_scene_element(scene: Scene, parent: ET.Element) -> ET.Element:
    """Creates an xml element of type scene.
    
    <scene human_readable_name="name" id="0">
      ...
    </scene>
    """
    return ET.SubElement(parent, "scene", attrib={
        "id": str(scene.id),
        "human_readable_name": scene.human_readable_name
    })


def _create_filter_element(filter: Filter, parent: ET.Element) -> ET.Element:
    """Creates an xml element of type filter.
    
    <filter type="0" id="id">
      ...
    </filter>
    
    TODO Expects Universe filter name to be 'Universe.x' to save filter with id=x. Other names will cause filter name to be wrong.
    """
    return ET.SubElement(parent, "filter", attrib={
        "id": filter.id,
        "type": str(filter.type)
    })


def _create_channel_link_element(channel_link: tuple[str, str], parent: ET.Element) -> ET.Element:
    """Creates an xml element of type channellink.
    
    <channellink input_channel_id="id" output_channel_id="id">
    """

    # Some nodes have input and output named value. Internally, the input is saved as 'value_in', but must be written as 'value'.
    return ET.SubElement(parent, "channellink", attrib={
        "input_channel_id": "value" if channel_link[0] == "value_in" else channel_link[0],
        "output_channel_id": channel_link[1]
    })


def _create_filter_configuration_element(filter_configuration: tuple[str, str], parent: ET.Element) -> ET.Element:
    """Creates an xml element of type filterConfiguration.
    
    <filterConfiguration name="key" value="value">
    """

    # if check for Universe node: Filter Configuration is saved backwards to display QLineEdit the right way
    key, value = filter_configuration
    return ET.SubElement(parent, "filterConfiguration", attrib={
        "name": key if "input_" not in key else value,
        "value": value if "input_" not in key else key
    })


def _create_inital_parameters_element(initial_parameter: tuple[str, str], parent: ET.Element) -> ET.Element:
    """Creates an xml element of type initalParameters.
    
    <initalParameters name="key" value="value">
    """
    return ET.SubElement(parent, "initialParameters", attrib={
        "name": initial_parameter[0],
        "value": initial_parameter[1]
    })


def _create_universe_element(universe: Universe, parent: ET.Element) -> ET.Element:
    """Creates an xml element of type physical_location.

    <universe name="name" description="description" id="0">
        ...
    </universe>
    """
    return ET.SubElement(parent, "universe", attrib={
        "id": str(universe.address),
        "name": universe.name,
        "description": universe.description
    })


def _create_physical_location_element(physical_location: int, parent: ET.Element) -> ET.Element:
    """Creates an xml element of type physical_location.

    <physical_location>0</physical_location>
    """
    pl = ET.SubElement(parent, "physical_location")
    pl.text = str(physical_location)
    return pl


def _create_artnet_location_element(self, artnet_location: proto.Universe.ArtNet, parent: ET.Element) -> ET.Element:
    """Creates an xml element of type artnet_location.
    
    <artnet_location ip_address="127.0.0.1" udp_port="666" device_universe_id="0" />
    """
    return ET.SubElement(parent, "artnet_location", attrib={
        "ip_address": artnet_location.ip_address,
        "udp_port": str(artnet_location.port),
        "device_universe_id": str(artnet_location.universe_on_device)
    })


def _create_ftdi_location_element(ftdi_location: proto.Universe.USBConfig, parent: ET.Element) -> ET.Element:
    """Creates an xml element of type ftdi_location.
    
    <ftdi_location vendor_id="0" product_id="0" device_name="name"/>
    """
    return ET.SubElement(parent, "ftdi_location", attrib={
        "vendor_id": ftdi_location.vendor_id,
        "product_id": str(ftdi_location.product_id),
        "device_name": ftdi_location.device_name,
        "serial_identifier": ftdi_location.serial
    })


def _create_device_element(device, parent: ET.Element) -> ET.Element:
    """TODO implement
    
    <device channel="0" name="name" type="type" universe_id="0">
    """
    pass


def _create_uihint_element(uihint: tuple[str, str], parent: ET.Element) -> ET.Element:
    """Creates an xml element of type uihint.
    
    <uihint name="key" value="value"/>
    """
    return ET.SubElement(parent, "uihint", attrib={
        "name": uihint[0],
        "value": uihint[1]
    })
