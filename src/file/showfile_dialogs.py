from PySide6.QtWidgets import QWidget, QFileDialog

from file.read import read_document
from file.write import write_document, create_xml
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
    file_dialog.fileSelected.connect(lambda file_name: func(file_name, show_data))
    file_dialog.show()


def _load_show_file(file_name: str, show_data: BoardConfiguration):
    """Loads a show file.

    Args:
        file_name: Path to the file to be loaded
    """
    if read_document(file_name, show_data):
        show_data.broadcaster.show_file_loaded.emit()


def _save_show_file(file_name: str, show_data: BoardConfiguration):
    """Saves the board configuration to specified file.

    Args:
        file_name: File in which the config is saved.
    """
    xml = create_xml(show_data)
    write_document(file_name, xml)


def show_save_showfile_dialog(parent: QWidget, show_data: BoardConfiguration):
    _select_file(parent, _save_show_file, True, show_data)


def show_load_showfile_dialog(parent: QWidget, show_data: BoardConfiguration):
    _select_file(parent, _load_show_file, False, show_data)
