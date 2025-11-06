"""Handle reading a xml document."""
import json
import os
import xml.etree.ElementTree as ET
from logging import getLogger
from uuid import UUID

import xmlschema
from defusedxml.ElementTree import parse

import proto.Console_pb2
import proto.UniverseControl_pb2
from controller.file.deserialization.migrations import replace_old_filter_configurations
from controller.file.deserialization.post_load_operations import link_patched_fixtures
from controller.utils.process_notifications import get_process_notifier
from model import BoardConfiguration, ColorHSI, Filter, Scene, UIPage, Universe
from model.control_desk import BankSet, ColorDeskColumn, FaderBank, RawDeskColumn
from model.events import EventSender, mark_sender_persistent
from model.filter import VirtualFilter
from model.macro import Macro, trigger_factory
from model.media_assets.asset_loading_factory import load_asset
from model.media_assets.factory_hint import AssetFactoryObjectHint
from model.media_assets.registry import clear as clear_media_registry
from model.ofl.fixture import load_fixture, make_used_fixture
from model.scene import FilterPage
from model.virtual_filters.vfilter_factory import construct_virtual_filter_instance
from utility import resource_path
from view.dialogs import ExceptionsDialog
from view.show_mode.show_ui_widgets import WIDGET_LIBRARY, filter_to_ui_widget

logger = getLogger(__name__)


def _parse_and_add_bankset(child: ET.Element, loaded_banksets: dict[str, BankSet]) -> None:
    """Parse and add a bank set to the show file.

    Args:
        child: The XML element to examine.
        loaded_banksets: The list to add the bank set to.

    """
    _id = child.attrib.get("id")
    bs: BankSet = BankSet(gui_controlled=True, id_=_id)
    for bank_element in child:
        bank = FaderBank()
        if bank_element.tag != "bank":
            logger.error("Unexpected element '%s' while parsing bank", bank_element.tag)
            continue
        for column_element in bank_element:
            if column_element.tag == "hslcolumn":
                col = ColorDeskColumn(_id=column_element.attrib["id"])
                col.display_name = column_element.attrib["display_name"]
                col.top_display_line_inverted = column_element.attrib.get("top_line_inverted") == "true"
                col.bottom_display_line_inverted = column_element.attrib.get("bottom_line_inverted") == "true"
                col.display_color = lcd_color_from_string(column_element.attrib["lcd_color"])
                col.color = ColorHSI.from_filter_str(column_element.attrib["color"])
            elif column_element.tag == "rawcolumn":
                col = RawDeskColumn(_id=column_element.attrib["id"])
                col.display_name = column_element.attrib["display_name"]
                col.top_display_line_inverted = column_element.attrib.get("top_line_inverted") == "true"
                col.bottom_display_line_inverted = column_element.attrib.get("bottom_line_inverted") == "true"
                col.display_color = lcd_color_from_string(column_element.attrib["lcd_color"])
                col.secondary_text_line = column_element.attrib["secondary_text_line"]
                col.fader_position = int(column_element.attrib["fader_position"])
                col.encoder_position = int(column_element.attrib["encoder_position"])
            else:
                logger.error("Unsupported bank column type '%s'.", column_element.tag)
                continue
            bank.add_column(col)
        bs.add_bank(bank)
    if child.attrib.get("linked_by_default") == "true":
        bs.link()
    loaded_banksets[bs.id] = bs


def read_document(file_name: str, board_configuration: BoardConfiguration) -> bool:
    """Parse the specified file to a board configuration data model.

    Args:
        file_name: The path to the file to parse.
        board_configuration: The current BoardConfiguration.

    Returns:
        A BoardConfiguration instance parsed from the provided file.

    """
    board_configuration.broadcaster.begin_show_file_parsing.emit()
    pn = get_process_notifier("Load Showfile", 5)

    try:
        pn.current_step_description = "Load file from disk."
        with open(resource_path(os.path.join("resources", "ShowFileSchema.xsd")), "r", encoding="UTF-8") as schema_file:
            schema = xmlschema.XMLSchema(schema_file)
        pn.current_step_number += 1
        schema.validate(file_name)
        pn.current_step_number += 1
    except Exception as error:
        logger.exception("Error while validating show file: %s", error)
        ExceptionsDialog(error).exec()
        board_configuration.broadcaster.end_show_file_parsing.emit()
        pn.close()
        return False

    clear_media_registry()
    board_configuration.broadcaster.clear_board_configuration.emit()
    pn.current_step_number += 1
    tree = parse(file_name)
    root = tree.getroot()

    prefix = ""

    pn.total_step_count += len(root.attrib.items())
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
                logger.warning("Found attribute %s=%s while parsing board configuration", key, value)
        pn.current_step_number += 1

    _clean_tags(root, prefix)

    scene_defs_to_be_parsed = []
    loaded_banksets: dict[str, BankSet] = {}

    pn.total_step_count += len(root)
    for child in root:
        match child.tag:
            case "scene":
                scene_defs_to_be_parsed.append(child)
            case "universe":
                _parse_universe(child, board_configuration)
            case "uihint":
                _parse_ui_hint(child, board_configuration)
            case "bankset":
                _parse_and_add_bankset(child, loaded_banksets)
            case "eventsource":
                _parse_and_add_event_source(child)
            case "macro":
                _parse_and_add_macro(child, board_configuration)
            case _:
                logger.warning("Show %s contains unknown element: %s", board_configuration.show_name, child.tag)
        pn.total_step_count += 1

    pn.total_step_count += len(scene_defs_to_be_parsed)
    for scene_def in scene_defs_to_be_parsed:
        _parse_scene(scene_def, board_configuration, loaded_banksets)
        pn.current_step_number += 1

    pn.current_step_number += 1

    link_patched_fixtures(board_configuration)
    pn.current_step_number += 2
    try:
        fader_value = int(board_configuration.ui_hints.get("default_main_brightness") or "255")
        board_configuration.broadcaster.request_main_brightness_fader_update.emit(fader_value)
    except ValueError as e:
        logger.exception("Unable to parse main brightness setting: %s", e)
    if board_configuration.ui_hints.get("media_assets"):
        load_all_media_assets(board_configuration.ui_hints.get("media_assets"), file_name)

    board_configuration.broadcaster.board_configuration_loaded.emit(file_name)
    board_configuration.file_path = file_name
    board_configuration.broadcaster.end_show_file_parsing.emit()
    board_configuration.broadcaster.show_file_loaded.emit()
    pn.close()
    return True


def lcd_color_from_string(display_color: str) -> proto.Console_pb2.lcd_color:
    """Convert the string representation of the LCD backlight color to the enum.

    Args:
        display_color: The string representation.

    Returns:
        The enum representation.

    """
    match display_color:
        case "white":
            return proto.Console_pb2.lcd_color.white
        case "red":
            return proto.Console_pb2.lcd_color.red
        case "blue":
            return proto.Console_pb2.lcd_color.blue
        case "cyan":
            return proto.Console_pb2.lcd_color.cyan
        case "black":
            return proto.Console_pb2.lcd_color.black
        case "green":
            return proto.Console_pb2.lcd_color.green
        case "magenta":
            return proto.Console_pb2.lcd_color.magenta
        case "yellow":
            return proto.Console_pb2.lcd_color.yellow
        case _:
            return proto.Console_pb2.lcd_color.white


def _clean_tags(element: ET.Element, prefix: str) -> None:
    """Recursively clean up immediate XML tag prefixes."""
    for child in element:
        child.tag = child.tag.replace(prefix, "")
        _clean_tags(child, prefix)


def _parse_filter_page(element: ET.Element, parent_scene: Scene, instantiated_pages: list[FilterPage]) -> bool:
    """Load a filter page from the XML representation.

    Args:
        element: The XML element to load the data from.
        parent_scene: The scene to add the page to.
        instantiated_pages: The list of all loaded filter pages, to which this element is appended.

    """
    f = FilterPage(parent_scene)
    for key, value in element.attrib.items():
        match key:
            case "name":
                f.name = str(value)
            case "parent":
                if value:
                    parent_page: FilterPage | None = None
                    for parent_candidate in instantiated_pages:
                        if parent_candidate.name == value:
                            parent_page = parent_candidate
                            break
                    if not parent_page:
                        return False

                    parent_page.child_pages.append(f)
                else:
                    parent_scene.insert_filterpage(f)
                instantiated_pages.append(f)
            case _:
                logger.warning(
                    "Found attribute %s=%s while parsing filter page for scene %s",
                    key,
                    value,
                    parent_scene.human_readable_name,
                )
    for child in element:
        if child.tag != "filterid":
            logger.error("Found unknown tag '%s' in filter page.", child.tag)
        else:
            filter_ = parent_scene.get_filter_by_id(child.text)
            if filter_:
                f.filters.append(filter_)
            else:
                logger.error("Didn't find filter '%s' in scene '%s'.", child.text, parent_scene.human_readable_name)
        # TODO load comments
    return True


def _parse_scene(
    scene_element: ET.Element, board_configuration: BoardConfiguration, loaded_banksets: dict[str, BankSet]
) -> None:
    """Load a scene from the show file data structure.

    Args:
        scene_element: The XML element to use.
        board_configuration: The show configuration object to insert the scene into.
        loaded_banksets: A list of bank sets associated with the scene.

    """
    human_readable_name = ""
    scene_id = 0
    for key, value in scene_element.attrib.items():
        match key:
            case "human_readable_name":
                human_readable_name = value
            case "id":
                scene_id = int(value)
            case _:
                logger.warning(
                    "Found attribute %s=%s while parsing scene for show %s", key, value, board_configuration.show_name
                )

    scene = Scene(scene_id=scene_id, human_readable_name=human_readable_name, board_configuration=board_configuration)

    filter_pages = []
    ui_page_elements = []
    for child in scene_element:
        match child.tag:
            case "filter":
                _parse_filter(child, scene)
            case "filterpage":
                filter_pages.append(child)
            case "uipage":
                ui_page_elements.append(child)
            case _:
                logger.warning("Scene %s contains unknown element: %s", human_readable_name, child.tag)

    i: int = 0
    instantiated_pages: list[FilterPage] = []
    while len(filter_pages) > 0:
        if _parse_filter_page(filter_pages[i], scene, instantiated_pages):
            filter_pages.remove(filter_pages[i])
            i = 0
        else:
            i += 1
            if i >= len(filter_pages):
                logger.error("No suitable parent found while parsing filter pages")
                break

    if scene_element.attrib.get("linkedBankset") in loaded_banksets:
        scene.linked_bankset = loaded_banksets[scene_element.attrib["linkedBankset"]]

    for ui_page_element in ui_page_elements:
        _append_ui_page(ui_page_element, scene)

    board_configuration.broadcaster.scene_created.emit(scene)


def _append_ui_page(page_def: ET.Element, scene: Scene) -> None:
    """Load a UI page (containing widgets) from XML data.

    Args:
        page_def: The XML data structure.
        scene: The scene to add it to.

    """
    page = UIPage(scene)
    for k, v in page_def.attrib.items():
        match k:
            case "title":
                page.title = str(v)
            case _:
                logger.error("Unexpected attribute '%s':'%s' in ui page definition.", k, v)
    for widget_def in page_def:
        pos_x: int = 0
        pos_y: int = 0
        w: int = 0
        h: int = 0
        fids = []
        conf: dict[str, str] = {}
        for k, v in widget_def.attrib.items():
            match k:
                case "posX":
                    pos_x = int(v)
                case "posY":
                    pos_y = int(v)
                case "sizeW":
                    w = int(v)
                case "sizeH":
                    h = int(v)
                case "filterID":
                    fids = str(v).split(":")
                case "variante":
                    widget_cdef = WIDGET_LIBRARY.get(str(v))
                case _:
                    logger.error("Unexpected attribute '%s':'%s' in ui widget definition.", k, v)
        for config_entry in widget_def:
            if config_entry.tag != "configurationEntry":
                logger.error("Found unexpected child '%s' in ui widget definition.", config_entry.tag)
                continue
            conf[str(config_entry.attrib["name"])] = str(config_entry.attrib["value"])
        filters = []
        for fid in fids:
            corresponding_filter = scene.get_filter_by_id(fid)
            if not corresponding_filter:
                logger.error(
                    "Did not load filter for ui widget with id '%s' from scene '%s' as it does not exist.",
                    fid,
                    scene,
                )
                continue
            filters.append(corresponding_filter)
        if widget_cdef is None:
            logger.warning("Opening legacy show file. Attempting to match scene UI widget by used filter.")
            ui_widget = filter_to_ui_widget(filters[0], page, conf)
        else:
            ui_widget = widget_cdef[1](page, conf)

        for i, f in enumerate(filters):
            ui_widget.set_filter(f, i)

        ui_widget.position = (pos_x, pos_y)
        ui_widget.size = (w, h)
        page.append_widget(ui_widget)
    scene.ui_pages.append(page)


def _parse_filter(filter_element: ET.Element, scene: Scene) -> None:
    """Load a filter from the XML definition.

    Args:
        filter_element: The XML data to load the filter from.
        scene: The scene to append the filter to.

    """
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
                pos = (float(value.split(",")[0]), float(value.split(",")[1]))
            case _:
                logger.warning(
                    "Found attribute %s=%s while parsing filter for scene %s", key, value, scene.human_readable_name
                )

    if filter_type < 0:
        filter_ = construct_virtual_filter_instance(scene, filter_type, filter_id, pos=pos)
    else:
        filter_ = Filter(scene=scene, filter_id=filter_id, filter_type=filter_type, pos=pos)

    for child in filter_element:
        match child.tag:
            case "channellink":
                _parse_channel_link(child, filter_)
            case "initialParameters":
                _parse_initial_parameters(child, filter_)
            case "filterConfiguration":
                _parse_filter_configuration(child, filter_, filter_.filter_configurations)
            case _:
                logger.warning("Filter %s contains unknown element: %s", filter_id, child.tag)

    filter_ = replace_old_filter_configurations(filter_)
    if isinstance(filter_, VirtualFilter):
        filter_.deserialize()
    scene.append_filter(filter_)


def _parse_channel_link(initial_parameters_element: ET.Element, filter_: Filter) -> None:
    """Load a connection between two filters.

    Args:
        initial_parameters_element: The XML element describing the connection.
        filter_: The parent filter (whose input this is) to attach the connection to.

    """
    cl_key = ""
    cl_value = ""
    for key, value in initial_parameters_element.attrib.items():
        match key:
            case "input_channel_id":
                cl_key = value
            case "output_channel_id":
                cl_value = value
            case _:
                logger.warning("Found attribute %s=%s while parsing key-value-pair", key, value)

    filter_.channel_links[cl_key] = cl_value


def _parse_initial_parameters(initial_parameters_element: ET.Element, filter_: Filter) -> None:
    """Load the parameters of a filter.

    Args:
        initial_parameters_element: The XML definition to load the parameters from.
        filter_: The filter whose parameters these are.

    """
    ip_key = ""
    ip_value = ""
    for key, value in initial_parameters_element.attrib.items():
        match key:
            case "name":
                ip_key = value
            case "value":
                ip_value = value
            case _:
                logger.warning(
                    "Found attribute %s=%s while parsing initial parameter for filter %s", key, value, filter_.filter_id
                )

    filter_.initial_parameters[ip_key] = ip_value


def _parse_filter_configuration(filter_configuration_element: ET.Element, filter_: Filter, fc: dict[str, str]) -> None:
    """Load the configuration of a filter.

    Args:
        filter_configuration_element: The XML data to load the configuration from.
        filter_: The filter to which the configuration belongs.
        fc: The existing configuration to append to.

    """
    fc_key = ""
    fc_value = ""
    for key, value in filter_configuration_element.attrib.items():
        match key:
            case "name":
                fc_key = value
            case "value":
                fc_value = value
            case _:
                logger.warning(
                    "Found attribute %s=%s while parsing filter configuration for filter %s",
                    key,
                    value,
                    filter_.filter_id,
                )

    fc[fc_key] = fc_value


def _parse_universe(universe_element: ET.Element, board_configuration: BoardConfiguration) -> None:
    """Load a universe description from XML data.

    Args:
        universe_element: The XML data to use.
        board_configuration: The show to register the universe with.

    """
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
                logger.warning(
                    "Found attribute %s=%s while parsing universe for show %s",
                    key,
                    value,
                    board_configuration.show_name,
                )

    if universe_id is None:
        logger.error("Could not parse universe element, id attribute is missing")

    physical = _parse_physical_location(pl) if (pl := universe_element.find("physical_location")) is not None else None
    artnet = _parse_artnet_location(an) if (an := universe_element.find("artnet_location")) is not None else None
    ftdi = _parse_ftdi_location(ftdi_l) if (ftdi_l := universe_element.find("ftdi_location")) is not None else None

    if physical is None and artnet is None and ftdi is None:
        logger.warning("Could not parse any location for universe %s", universe_id)

    universe_proto = proto.UniverseControl_pb2.Universe(
        id=universe_id, physical_location=physical, remote_location=artnet, ftdi_dongle=ftdi
    )

    universe = Universe(universe_proto)
    universe.name = name
    universe.description = description

    if patching := universe_element.find("patching"):
        _parse_patching(board_configuration, patching, universe_id)


def _parse_physical_location(location_element: ET.Element) -> int:
    """Parse a universe definition for one attached directly to the IO mainboard.

    Args:
        location_element: The XML data to load from.

    Returns:
        The location.

    """
    return int(location_element.text)


def _parse_artnet_location(location_element: ET.Element) -> proto.UniverseControl_pb2.Universe.ArtNet:
    """Parse a universe definition of an ArtNet stage box.

    Args:
        location_element: The XML data to load from.

    Returns:
        An ArtNet universe location.

    """
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
                logger.warning("Found attribute %s=%s while parsing artnet location", key, value)

    return proto.UniverseControl_pb2.Universe.ArtNet(
        ip_address=ip_address, port=udp_port, universe_on_device=device_universe_id
    )


def _parse_ftdi_location(location_element: ET.Element) -> proto.UniverseControl_pb2.Universe.USBConfig:
    """Load a universe location definition of a USB DMX adapter.

    Args:
        location_element: The XML data to load from.

    Returns:
        The loaded connection details.

    """
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
                logger.warning("Found attribute %s=%s while parsing ftdi location", key, value)

    return proto.UniverseControl_pb2.Universe.USBConfig(
        product_id=product_id, vendor_id=vendor_id, device_name=device_name, serial=serial_identifier
    )


def _parse_patching(board_configuration: BoardConfiguration, location_element: ET.Element, universe_id: int) -> None:
    """Load patching information from XML data.

    Args:
        board_configuration: The current BoardConfiguration.
        location_element: The XML data to load from.
        universe_id: The ID of the universe this fixture belongs to.

    Returns:
        The loaded fixtures.

    """
    fixtures_path = "/var/cache/missionDMX/fixtures"  # TODO config file

    for child in location_element:
        make_used_fixture(
            board_configuration,
            load_fixture(os.path.join(fixtures_path, child.attrib["fixture_file"])),
            int(child.attrib["mode"]),
            board_configuration.universe(universe_id),
            int(child.attrib["start"]),
            UUID(child.attrib.get("id")) if child.attrib.get("id") else None,
            child.attrib.get("color"),
        )

    # TODO load fixture name from file


def _parse_ui_hint(ui_hint_element: ET.Element, board_configuration: BoardConfiguration) -> None:
    """Load general configuration data.

    Args:
        ui_hint_element: The XML representation to load from.
        board_configuration: The show file to apply the settings on.

    """
    ui_hint_key = ""
    ui_hint_value = ""
    for key, value in ui_hint_element.attrib.items():
        match key:
            case "name":
                ui_hint_key = value
            case "value":
                ui_hint_value = value
            case _:
                logger.warning("Found attribute %s=%s while parsing ui hint", key, value)

    board_configuration.ui_hints[ui_hint_key] = ui_hint_value


def _parse_and_add_event_source(elm: ET.Element) -> None:
    name = "undef"
    stype = "fish.builtin.plain"
    for key, value in elm.attrib.items():
        match key:
            case "id":
                name = value
            case "name":
                pass  # as we treat the id and the name to be the same thing for now.
            case "type":
                stype = value
            case _:
                logger.error("Unexpected attribute in event source '%s'='%s'.", key, value)
    evs = EventSender(name)
    evs.type = stype
    for child in elm:
        match child.tag:
            case "configuration":
                evs.configuration[str(child.attrib["name"])] = str(child.attrib["value"])
            case "eventRename":
                evs.renamed_events[
                    (
                        int(child.attrib["eventType"]),
                        int(child.attrib["senderFunction"]),
                        str(child.attrib["arguments"]),
                    )
                ] = child.text
            case _:
                logger.error("Unexpected child in event source definition: %s.", child.tag)
    mark_sender_persistent(name, evs.renamed_events)
    evs.send_update(auto_commit=True, push_direct=True)


def _parse_and_add_macro(elm: ET.Element, board_configuration: BoardConfiguration) -> None:
    m = Macro(board_configuration)
    m.name = elm.attrib["name"]
    for child in elm:
        match child.tag:
            case "content":
                m.content = str(child.text)
            case "trigger":
                t = trigger_factory(child.attrib["type"])
                t.name = child.attrib["name"]
                m.add_trigger(t, child.attrib["enabled"].lower() == "true")
                for conf_entry in child:
                    t.set_param(conf_entry.attrib["name"], conf_entry.attrib["value"])
            case _:
                logger.error("Unexpected child in macro definition: %s.", child.tag)
    board_configuration.add_macro(m)

def load_all_media_assets(media_asset_defintion: str, show_file_path: str) -> None:
    """Load media assets from provided UI hint."""
    assets = json.loads(media_asset_defintion)
    for asset in assets:
        load_asset(
            asset.get("uuid", ""),
            AssetFactoryObjectHint(asset.get("type_hint", "")),
            asset.get("data", ""),
            show_file_path=show_file_path,
            name=asset.get("name", "")
        )
