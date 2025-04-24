# coding=utf-8
from xml.etree import ElementTree

from controller.file.serializing.events_and_macros import _write_event_sender, _write_macro
from controller.file.serializing.scene_serialization import generate_scene_xml_description
from controller.file.serializing.ui_settings_serialization import _create_ui_hint_element
from controller.file.serializing.universe_serialization import (_create_artnet_location_element,
                                                                _create_ftdi_location_element, _create_patching_element,
                                                                _create_physical_location_element,
                                                                _create_universe_element)
from controller.utils.process_notifications import ProcessNotifier
from model import BoardConfiguration
from model.events import get_all_senders


def create_xml(board_configuration: BoardConfiguration, pn: ProcessNotifier,
               assemble_for_fish_loading: bool = False) -> ElementTree.Element:
    """Creates a xml element from the given board configuration.

    Args:
        board_configuration: The board configuration to be converted.
        assemble_for_fish_loading: Pass True if the XML is build for fish. This will skip UI and resolve virtual filters

    Returns:
        The xml element containing the board configuration.
        See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd for more information
    """
    pn.current_step_description = "Creating document root."
    pn.total_step_count += 1 + len(board_configuration.scenes) + 3
    root = _create_board_configuration_element(board_configuration)
    pn.current_step_description = "Writing scenes."
    pn.current_step_number += 1

    for scene in board_configuration.scenes:
        generate_scene_xml_description(assemble_for_fish_loading, root, scene, pn)
        pn.total_step_count += 1

    pn.current_step_description = "Creating universes."
    for universe in board_configuration.universes:
        universe_element = _create_universe_element(universe=universe, parent=root)

        proto = universe.universe_proto

        if proto.remote_location.ip_address != "":
            _create_artnet_location_element(artnet_location=proto.remote_location, parent=universe_element)
        elif proto.ftdi_dongle.vendor_id != "":
            _create_ftdi_location_element(ftdi_location=proto.ftdi_dongle, parent=universe_element)
        else:
            _create_physical_location_element(physical=proto.physical_location, parent=universe_element)

        _create_patching_element(patching=universe.patching, parent=universe_element,
                                 assemble_for_fish=assemble_for_fish_loading)
    pn.total_step_count += 1
    pn.current_step_description = "Storing device list."

    for device in board_configuration.devices:
        _create_device_element(device=device, parent=root)
    pn.total_step_count += 1

    pn.current_step_description = "Saving GUI state."
    if not assemble_for_fish_loading:
        for ui_hint in board_configuration.ui_hints.items():
            _create_ui_hint_element(ui_hint=ui_hint, parent=root)
        for event_source in get_all_senders():
            _write_event_sender(root, event_source)
        for m in board_configuration.macros:
            _write_macro(root, m)
    pn.total_step_count += 1

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


def _create_device_element(device, parent: ElementTree.Element) -> ElementTree.Element:
    """TODO implement patching of devices

    <device channel="0" name="name" type="type" universe_id="0">
    """
