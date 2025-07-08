"""Dialogs for Show File"""
import os

from PySide6.QtWidgets import QFileDialog, QWidget

from controller.file.read import read_document
from controller.file.write import write_document
from model import BoardConfiguration


def _select_file(parent: QWidget, func, show_save_dialog: bool, show_data: BoardConfiguration) -> None:
    """Opens QFileDialog to select a file.

    Args:
        func: Function to be called after file was selected and confirmed. Function gets the file name as a string.
    """
    file_dialog = QFileDialog(parent, "Save Show File" if show_save_dialog else "Load Show File")
    file_dialog.setNameFilter("Mission DMX Show Files (*.show)")
    if show_save_dialog:
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    file_dialog.setDefaultSuffix(".show")
    file_dialog.setDirectory(os.path.expanduser("~"))
    file_dialog.fileSelected.connect(lambda file_name: func(file_name, show_data))
    file_dialog.show()


def _load_show_file(file_name: str, show_data: BoardConfiguration) -> None:
    """Loads a show file.

    Args:
        file_name: Path to the file to be loaded
    """
    if read_document(file_name, show_data):
        show_data.broadcaster.show_file_loaded.emit()


def _save_show_file(file_name: str, show_data: BoardConfiguration) -> None:
    """Saves the board configuration to a specified file.

    Args:
        file_name: File in which the config is saved.
    """
    if write_document(file_name, show_data) and show_data.file_path != file_name:
        show_data.file_path = file_name


def show_save_showfile_dialog(parent: QWidget, show_data: BoardConfiguration):
    """
    Open the save file dialog if required and save the file.
    :param parent: The parent of the show file
    :param show_data: The show content to be saved
    """
    _select_file(parent, _save_show_file, True, show_data)


def show_load_showfile_dialog(parent: QWidget, show_data: BoardConfiguration):
    """
    Display the open file dialog to open a show file and load it if one was successfully selected.
    :param parent: The parent widget of the dialog
    :param show_data: The show file configuration to load the data into.
    """
    _select_file(parent, _load_show_file, False, show_data)
