
"""This file provides the about-dialog"""
import os.path
from logging import getLogger

import tomlkit
from html2text import html2text
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from utility import resource_path

logger = getLogger(__file__)

with open(resource_path(os.path.join("resources", 'pyproject.toml')), 'r', encoding="UTF-8") as f:
    data = tomlkit.load(f)


def read_entire_file_as_str(file_path: str) -> str:
    """Read the content of a text file and return the content as-is.
    This method does not throw IO errors but may return a debug hint and log the issue in case something goes wrong.

    :param file_path: The path to the file to load
    :returns: The content of the loaded file or a hint that something went wrong.
    """
    # TODO in toml
    try:
        with open(file_path, 'r', encoding='UTF-8') as f:
            text = f.read()
    except OSError as e:
        text = "Unknown Debug"
        logger.error("Unable to load file string from %s. %s", file_path, e)
    return text


VERSION_STR = data['project']['version']
CONTRIBUTORS_STR = html2text(read_entire_file_as_str(resource_path(os.path.join("resources", "contributors.html"))))


class AboutWindow(QMessageBox):
    """
    This window displays the credits.
    """

    def __init__(self, parent):
        super().__init__(
            QMessageBox.Icon.Information,
            "<b>About</b>",
            f"<i>MissionDMX</i> - Version {VERSION_STR}",
            parent=parent)
        self.setStandardButtons(QMessageBox.StandardButton.Close)
        self.setInformativeText('<br>The Manual for this software can be found by clicking the help button or by '
                                'visiting <a href="https://github.com/Mission-DMX/Docs/blob/main/Editor/Readme.md">'
                                'the online manual</a>.<br>Copyright (c) the MissionDMX contributors')
        self.setDetailedText(CONTRIBUTORS_STR)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setTextFormat(Qt.RichText)
