# coding=utf-8
"""Handles reading a xml document"""

import os
import random
from xml.etree import ElementTree

import xmlschema

import proto.UniverseControl_pb2 as Proto
from file import logger
from model import Filter, Scene, Universe, BoardConfiguration, PatchingUniverse, UIPage, ColorHSI
from model.control_desk import BankSet, FaderBank, ColorDeskColumn, RawDeskColumn
from model.scene import FilterPage
from controller.ofl.fixture import load_fixture, UsedFixture, make_used_fixture
from proto.Console_pb2 import lcd_color
from view.dialogs import ExceptionsDialog
from view.show_mode.editor.show_ui_widgets import filter_to_ui_widget


logger = logging.getLogger(__name__)


def _parse_and_add_bankset(child: ElementTree.Element, loaded_banksets: dict[str, BankSet]):
    _id = child.attrib.get('id')
    bs: BankSet = BankSet(gui_controlled=True, id=_id)
    for bank_element in child:
        bank = FaderBank()
        if bank_element.tag != 'bank':
            logger.error("Unexpected element '{}' while parsing bank".format(bank_element.tag))
            continue
        for column_element in bank_element:
            if column_element.tag == 'hslcolumn':
                col = ColorDeskColumn(_id=column_element.attrib['id'])
                col.display_name = column_element.attrib['display_name']
                col.top_display_line_inverted = column_element.attrib.get('top_line_inverted') == 'true'
                col.bottom_display_line_inverted = column_element.attrib.get('bottom_line_inverted') == 'true'
                col.display_color = lcd_color_from_string(column_element.attrib['lcd_color'])
                col.color = ColorHSI.from_filter_str(column_element.attrib['color'])
            elif column_element.tag == 'rawcolumn':
                col = RawDeskColumn(_id=column_element.attrib['id'])
                col.display_name = column_element.attrib['display_name']
                col.top_display_line_inverted = column_element.attrib.get('top_line_inverted') == 'true'
                col.bottom_display_line_inverted = column_element.attrib.get('bottom_line_inverted') == 'true'
                col.display_color = lcd_color_from_string(column_element.attrib['lcd_color'])
                col.secondary_text_line = column_element.attrib['secondary_text_line']
                col.fader_position = int(column_element.attrib['fader_position'])
                col.encoder_position = int(column_element.attrib['encoder_position'])
            else:
                logger.error("Unsupported bank column type '{}'.".format(column_element.tag))
                continue
            bank.add_column(col)
        bs.add_bank(bank)
    if child.attrib.get('linked_by_default') == 'true':
        bs.link()
    loaded_banksets[bs.id] = bs
    pass


def read_document(file_name: str, board_configuration: BoardConfiguration) -> bool:
    """Parses the specified file to a board configuration data model.
    
    Args:
        file_name: The path to the file to be parsed.
        
    Returns:
        A BoardConfiguration instance parsed from the provided file.
    """

    try:
        schema_file = open("resources/ShowFileSchema.xsd", 'r')

        schema = xmlschema.XMLSchema(schema_file)
        schema.validate(file_name)
    except Exception as error:
        logger.error("Error while validating show file: {}".format(error))
        ExceptionsDialog(error).exec()
        return False

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
                logger.warning("Found attribute %s=%s while parsing board configuration", key, value)

    _clean_tags(root, prefix)

    scene_defs_to_be_parsed = []
    loaded_banksets: dict[str, BankSet] = {}

    for child in root:
        match child.tag:
            case "scene":
                scene_defs_to_be_parsed.append(child)
            case "device":
                _parse_device(child, board_configuration)
            case "universe":
                _parse_universe(child, board_configuration)
            case "uihint":
                _parse_ui_hint(child, board_configuration)
            case 'bankset':
                _parse_and_add_bankset(child, loaded_banksets)
            case _:
                logger.warning("Show %s contains unknown element: %s",
                                board_configuration.show_name, child.tag)

    for scene_def in scene_defs_to_be_parsed:
        _parse_scene(scene_def, board_configuration, loaded_banksets)

    board_configuration.broadcaster.board_configuration_loaded.emit(file_name)
    board_configuration.file_path = file_name
    return True


def lcd_color_from_string(display_color: str) -> lcd_color:
    match display_color:
        case 'white':
            return lcd_color.white
        case 'red':
            return lcd_color.red
        case 'blue':
            return lcd_color.blue
        case 'cyan':
            return lcd_color.cyan
        case 'black':
            return lcd_color.black
        case 'green':
            return lcd_color.green
        case 'magenta':
            return lcd_color.magenta
        case 'yellow':
            return lcd_color.yellow
        case _:
            return lcd_color.white


def _clean_tags(element: ElementTree.Element, prefix: str):
    for child in element:
        child.tag = child.tag.replace(prefix, '')
        _clean_tags(child, prefix)


def _parse_filter_page(element: ElementTree.Element, parent_scene: Scene, instantiated_pages: list[FilterPage]):
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
                    else:
                        parent_page.child_pages.append(f)
                else:
                    parent_scene.insert_filterpage(f)
                instantiated_pages.append(f)
            case _:
                logger.warning(
                    "Found attribute %s=%s while parsing filter page for scene %s",
                    key, value, parent_scene.human_readable_name)
    for child in element:
        if child.tag != "filterid":
            logger.error("Found unknown tag '{}' in filter page.".format(child.tag))
        else:
            filter = parent_scene.get_filter_by_id(child.text)
            if filter:
                f.filters.append(filter)
            else:
                logger.error("Didn't find filter '{}' in scene '{}'.".format(child.text,
                                                                              parent_scene.human_readable_name))
    return True


def _parse_scene(scene_element: ElementTree.Element, board_configuration: BoardConfiguration,
                 loaded_banksets: dict[str, BankSet]):
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
                    "Found attribute %s=%s while parsing scene for show %s",
                    key, value, board_configuration.show_name)

    scene = Scene(scene_id=scene_id,
                  human_readable_name=human_readable_name,
                  board_configuration=board_configuration)

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
                logger.warning("Scene %s contains unknown element: %s",
                                human_readable_name, child.tag)

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

    if scene_element.attrib.get('linkedBankset') in loaded_banksets.keys():
        scene.linked_bankset = loaded_banksets[scene_element.attrib['linkedBankset']]

    for ui_page_element in ui_page_elements:
        _append_ui_page(ui_page_element, scene)

    board_configuration.broadcaster.scene_created.emit(scene)


def _append_ui_page(page_def: ElementTree.Element, scene: Scene):
    page = UIPage(scene)
    for k, v in page_def.attrib.items():
        match k:
            case 'title':
                page.title = str(v)
            case _:
                logger.error("Unexpected attribute '{}':'{}' in ui page definition.".format(k, v))
    for widget_def in page_def:
        posX: int = 0
        posY: int = 0
        w: int = 0
        h: int = 0
        fid: str = ""
        variante: str = ""
        conf: dict[str, str] = {}
        for k, v in widget_def.attrib.items():
            match k:
                case "posX":
                    posX = int(v)
                case "posY":
                    posY = int(v)
                case "sizeW":
                    w = int(v)
                case "sizeH":
                    h = int(v)
                case "filterID":
                    fid = str(v)
                case "variante":
                    variante = str(v)
                case _:
                    logger.error("Unexpected attribute '{}':'{}' in ui widget definition.".format(k, v))
        for config_entry in widget_def:
            if config_entry.tag != "configurationEntry":
                logger.error("Found unexpected child '{}' in ui widget definition.".format(config_entry.tag))
                continue
            conf[str(config_entry.attrib['name'])] = str(config_entry.attrib['value'])
        corresponding_filter = scene.get_filter_by_id(fid)
        if not corresponding_filter:
            logger.error("Did not load ui widget for filter with id '{}' from scene '{}' as it does not exist."
                         .format(fid, scene))
            continue
        ui_widget = filter_to_ui_widget(corresponding_filter, page, conf, variante)
        ui_widget.position = (posX, posY)
        ui_widget.size = (w, h)
        page.append_widget(ui_widget)
    scene.ui_pages.append(page)


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
                pos = (float(value.split(",")[0]), float(value.split(",")[1]))
            case _:
                logger.warning(
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
                logger.warning("Filter %s contains unknown element: %s", filter_id, child.tag)

    scene.append_filter(filter_)


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
                logger.warning("Found attribute %s=%s while parsing key-value-pair", key, value)

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
                logger.warning("Found attribute %s=%s while parsing initial parameter for filter %s",
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
                logger.warning("Found attribute %s=%s while parsing filter configuration for filter %s",
                                key, value, filter_.filter_id)

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
                logger.warning("Found attribute %s=%s while parsing universe for show %s",
                                key, value, board_configuration.show_name)

    if universe_id is None:
        logger.error("Could not parse universe element, id attribute is missing")

    physical: int | None = None
    artnet: Proto.Universe.ArtNet | None = None
    ftdi: Proto.Universe.ArtNet | None = None
    patching = None

    for child in universe_element:
        match child.tag:
            case "physical_location":
                physical = _parse_physical_location(child)
            case "artnet_location":
                artnet = _parse_artnet_location(child)
            case "ftdi_location":
                ftdi = _parse_ftdi_location(child)
            case "patching":
                patching = _parse_patching(child, universe_id)

            case _:
                logger.warning("Universe %s contains unknown element: %s",
                                universe_id, child.tag)

    if physical is None and artnet is None and ftdi is None:
        logger.warning("Could not parse any location for universe %s", universe_id)

    universe_proto = Proto.Universe(id=universe_id,
                                    physical_location=physical,
                                    remote_location=artnet,
                                    ftdi_dongle=ftdi)
    patching_universe = PatchingUniverse(universe_proto)
    universe = Universe(patching_universe)
    universe.name = name
    universe.description = description
    if patching:
        for index, fixture in patching:
            current_channel = index
            color = "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
            for index in range(len(fixture.mode['channels'])):
                item = patching_universe.patching[current_channel + index]
                item.fixture = fixture
                item.fixture_channel = index
                item.color = color

    board_configuration.broadcaster.fixture_patched.emit()
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
                logger.warning("Found attribute %s=%s while parsing artnet location", key, value)

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
                logger.warning("Found attribute %s=%s while parsing ftdi location", key, value)

    return Proto.Universe.USBConfig(product_id=product_id,
                                    vendor_id=vendor_id,
                                    device_name=device_name,
                                    serial=serial_identifier)


def _parse_patching(location_element: ElementTree.Element, universe_id: int) -> list[tuple[int, UsedFixture]]:
    fixtures_path = '/var/cache/missionDMX/fixtures'
    used_fixtures: list[tuple[int, UsedFixture]] = []
    for child in location_element:
        used_fixture = make_used_fixture(load_fixture(os.path.join(fixtures_path, child.attrib['fixture_file'])),
                                         int(child.attrib['mode']), universe_id)

        used_fixtures.append((int(child.attrib['start']), used_fixture))

    return used_fixtures


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
                logger.warning("Found attribute %s=%s while parsing ui hint", key, value)

    board_configuration.ui_hints[ui_hint_key] = ui_hint_value
