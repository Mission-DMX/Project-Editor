"""Transmitting data as XML to Fish."""
from logging import getLogger

from controller.file.serializing.general_serialization import create_xml
from controller.network import NetworkManager
from controller.utils.process_notifications import get_process_notifier
from model import BoardConfiguration

logger = getLogger(__name__)


def transmit_to_fish(show: BoardConfiguration, goto_default_scene: bool = True) -> bool:
    """Send the current board configuration as an XML file to fish."""
    if not NetworkManager().connection_state():
        logger.error("Fish is not connected. Therefore we cannot transmit a show to it.")
        return False
    # TODO this could be an external QThread
    pn = get_process_notifier("Uploading Show to Fish", len(show.scenes))
    pn.current_step_description = "Checking for unlinked fader bank sets."
    for scene in show.scenes:
        if scene.linked_bankset:
            if not scene.linked_bankset.is_linked:
                scene.linked_bankset.link()
            if scene.linked_bankset.update_required:
                scene.linked_bankset.update()
        pn.current_step_number += 1
    xml = create_xml(show, pn, assemble_for_fish_loading=True)
    # TODO query current active scene
    show.broadcaster.transmitting_show_file.emit(xml, goto_default_scene)
    # TODO jump to current active scene and active bank set
    # TODO implement error handling
    pn.close()
    show.broadcaster.show_file_applied.emit()  # TODO make sure this only gets called if there was no error
    return True
