from controller.file.serializing.general_serialization import create_xml
from model import BoardConfiguration


def transmit_to_fish(show: BoardConfiguration, goto_default_scene: bool = True) -> bool:
    """Send the current board configuration as a xml file to fish"""
    for scene in show.scenes:
        if scene.linked_bankset:
            if not scene.linked_bankset.is_linked:
                scene.linked_bankset.link()
    xml = create_xml(show, assemble_for_fish_loading=True)
    # TODO query current active scene
    show.broadcaster.load_show_file.emit(xml, goto_default_scene)
    # TODO jump to current active scene and active bank set
    # TODO implement error handling
    return True
