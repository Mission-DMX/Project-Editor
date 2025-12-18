"""Unit test utils.

This module requires a config.py to be in the same package. This config file needs to contain a variable called
FISH_EXEC_PATH pointing to a local fish binary.
"""
import os.path
import subprocess
from logging import getLogger
from time import sleep

from PySide6.QtWidgets import QApplication

import proto.FilterMode_pb2
from controller.file.serializing.general_serialization import create_xml
from controller.network import NetworkManager
from controller.utils.process_notifications import get_process_notifier
from model import BoardConfiguration, Broadcaster

from .config import FISH_EXEC_PATH

logger = getLogger(__name__)

def _stall_until_stdout_reached_target(process: subprocess.Popen, target: str):
    while True:
        output = process.stdout.readline()
        if not output and process.poll() is not None:
            return False
        if target in output:
            return True


_last_error_message = ""
_GOOD_MESSAGES = ["No Error occured", "Showfile Applied"]

def execute_board_configuration(bc: BoardConfiguration, cycles: int = 25, recorded_gui_updates: list[tuple[int, str, str, str]] | None = None, main_brightness: int = 65565) -> bool:
    """Execute a board configuration.
    
    This method starts a fish instance, connects to it, uploads a board configuration and enables filter execution.
    If after the specified amount of iterations, no error occurred, the method stops, returning true. Otherwise, false.
    
    Args:
        bc: The board configuration to apply
        cycles: The amount of cycles to wait
        recorded_gui_updates: If A list is provided, any GUI updates received during execution are stored in there.
        main_brightness: The Main brightness value used for the test.
    
    Returns:
        True if no error occurred during execution. Otherwise, false.
    
    """
    global _last_error_message
    _last_error_message = _GOOD_MESSAGES[0]
    logger.debug("Starting fish...")
    if os.path.exists("/tmp/fish.sock"):
        logger.warning("Removing fish socket.")
        os.remove("/tmp/fish.sock")
    process = subprocess.Popen(
        [FISH_EXEC_PATH],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    _stall_until_stdout_reached_target(process, "[debug] Entering ev defloop")
    logger.debug("Starting QApplication...")
    application = QApplication([])
    logger.debug("Starting network manager.")
    nm = NetworkManager()
    def fish_error_received(msg: str):
        global _last_error_message
        if msg != _last_error_message:
            if msg not in _GOOD_MESSAGES:
                logger.error("Received error from fish: '%s'", msg)
        _last_error_message = msg
    nm.status_updated.connect(fish_error_received)
    broadcaster = Broadcaster()
    application.processEvents()
    logger.debug("Connecting to fish...")
    nm.start()
    application.processEvents()
    error_occurred: bool = False

    def receive_update_from_fish(msg: proto.FilterMode_pb2.update_parameter):
        if recorded_gui_updates is not None:
            recorded_gui_updates.append((msg.scene_id, msg.filter_id, msg.parameter_key, msg.parameter_value))

    broadcaster.update_filter_parameter.connect(receive_update_from_fish)
    for i in range(10):
        application.processEvents()
        sleep(0.01)
    pn = get_process_notifier("test upload notifier", 300)
    logger.info("Creating Show XML...")
    xml = create_xml(bc, pn, assemble_for_fish_loading=True)
    logger.info("Sending it to fish...")
    nm.transmit_show_file(xml, True)
    while _last_error_message == _GOOD_MESSAGES[0] and nm.connection_state():
        application.processEvents()
        sleep(0.01)
    if _last_error_message != _GOOD_MESSAGES[1]:
        error_occurred = True
    nm.set_main_brightness_fader_position(int((main_brightness / 65565) * 255))
    logger.info("Evaluating execution...")
    if not error_occurred:
        for i in range(cycles * 4):
            application.processEvents()
            sleep(0.01)
    logger.info("Ending execution...")
    nm.disconnect()
    sleep(1)
    del broadcaster
    del nm
    del application
    process.stdin.write("k\n")
    process.communicate()
    return process.returncode == 0 and not error_occurred
