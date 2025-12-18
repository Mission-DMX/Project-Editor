"""Unit test utils.

This module requires a config.py to be in the same package. This config file needs to contain a variable called
FISH_EXEC_PATH pointing to a local fish binary.
"""
import subprocess

from model import BoardConfiguration

from .config import FISH_EXEC_PATH

def _stall_until_stdout_reached_target(process: subprocess.Popen, target: str):
    while True:
        output = process.stdout.read(1024)
        if not output and process.poll() is not None:
            return False
        if target in output.decode():
            return True


def execute_board_configuratiuon(bc: BoardConfiguration, cycles: int = 25, recorded_gui_updates: list[tuple[int, str, str]] | None = None, main_brightness: int = 65565) -> bool:
    """Execute a board configuration.
    
    This method starts a fish instance, connects to it, uploads a board configuration and enables filter execution.
    If after the specified amount of iterations, no error occurred, the method stops, returning true. Otherwise false.
    
    Args:
        bc: The board configuration to apply
        cycles: The amount of cycles to wait
        recorded_gui_updates: If A list is provided, any GUI updates received during execution are stored in there.
        main_brightness: The Main brightness value used for the test.
    
    Returns:
        True if no error occurred during execution. Otherwise, false.
    
    """
    process = subprocess.Popen(
        [FISH_EXEC_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    _stall_until_stdout_reached_target(process, "[debug] Entering ev defloop")
    # TODO create network manager instance
    # TODO call send to fish method
    # TODO wait for response and abort if error received
    # TODO set main_brightness
    # TODO wait for cycles * 40 ms and record gui messages
    # TODO disconnect client and close QT Application
    # TODO stop fish by sending enter to stdin
    # TODO wait for fish to stop and return result
