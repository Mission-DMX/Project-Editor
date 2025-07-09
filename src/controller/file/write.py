"""Module to convert a board configuration to a xml element.

Usage:
    xml = createXML(board_configuration)
    writeDocument("ShowFiles/show_file.xml", xml)
"""
import os
from shutil import copyfile
from xml.etree import ElementTree as ET

from controller.file.serializing.general_serialization import create_xml
from controller.utils.process_notifications import get_process_notifier
from model import BoardConfiguration


def write_document(file_name: str, show_data: BoardConfiguration) -> bool:
    """Writes the xml element to the specified file.
    See https://github.com/Mission-DMX/Docs/blob/main/FormatSchemes/ProjectFile/ShowFile_v0.xsd for more information.
    
    Args:
        file_name: The (path and) file to which the xml element should be written.
        show_data: The show to save
        
    Returns: True, if successfully, otherwise false with error message.
    """
    pn = get_process_notifier("Saving Showfile", 2)
    xml = create_xml(show_data, pn)
    if os.path.exists(file_name):
        # TODO introduce proper version control
        copyfile(file_name, os.path.splitext(file_name)[0] + ".show_backup")
    pn.current_step_description = "Writing to disk."
    pn.current_step_number += 1
    with open(file_name, "w+", encoding="UTF-8") as file:
        ET.indent(xml)
        file.write(ET.tostring(xml, encoding="unicode", method="xml"))
    pn.current_step_number += 1
    pn.close()
    return True
    # try:
    #
    #    return True
    # except IOError:
    #    print(f"Could not save {file_name}")
    #    return False
