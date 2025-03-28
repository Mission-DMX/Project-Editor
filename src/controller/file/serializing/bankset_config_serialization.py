# coding=utf-8
import logging
from xml.etree import ElementTree

import proto.Console_pb2 
from model import Scene
from model.control_desk import ColorDeskColumn, RawDeskColumn


def lcd_color_to_string(display_color: proto.Console_pb2.lcd_color) -> str:
    match display_color:
        case proto.Console_pb2.lcd_color.white:
            return 'white'
        case proto.Console_pb2.lcd_color.red:
            return 'red'
        case proto.Console_pb2.lcd_color.blue:
            return 'blue'
        case proto.Console_pb2.lcd_color.cyan:
            return 'cyan'
        case proto.Console_pb2.lcd_color.black:
            return 'black'
        case proto.Console_pb2.lcd_color.green:
            return 'green'
        case proto.Console_pb2.lcd_color.magenta:
            return 'magenta'
        case proto.Console_pb2.lcd_color.yellow:
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
