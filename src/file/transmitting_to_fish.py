# coding=utf-8
from file.write import create_xml
from model import BoardConfiguration


def transmit_to_fish(show: BoardConfiguration, goto_default_scene: bool = True) -> bool:
    """Send the current board configuration as a xml file to fish"""
    for scene in show.scenes:
        if scene.linked_bankset:
            if not scene.linked_bankset.is_linked:
                scene.linked_bankset.link()
    xml = create_xml(show)
    show.broadcaster.load_show_file.emit(xml, goto_default_scene)
    # TODO implement error handling
    return True
