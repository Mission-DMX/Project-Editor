# coding=utf-8

"""This file provides the about-dialog"""

from logging import getLogger

from html2text import html2text
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

logger = getLogger(__file__)


def read_entire_file_as_str(file_path: str) -> str:
    """Read the content of a text file and return the content as-is.
    This method does not throw IO errors but may return a debug hint and log the issue in case something goes wrong.

    :param file_path: The path to the file to load
    :returns: The content of the loaded file or a hint that something went wrong.
    """
    try:
        with open(file_path, 'r') as f:
            text = f.read()
    except IOError as e:
        text = "Unknown Debug"
        logger.error("Unable to load file string from {}.".format(file_path), e)
    return text


VERSION_STR = read_entire_file_as_str("resources/version.txt")
CONTRIBUTORS_STR = html2text(read_entire_file_as_str("resources/contributors.html"))


class AboutWindow(QMessageBox):
    """
    This window displays the credits.
    """
    def __init__(self, parent):
        super().__init__(
            QMessageBox.Icon.Information,
            "<b>About</b>",
            "<i>MissionDMX</i> - Version {}".format(VERSION_STR),
            parent=parent)
        self.setStandardButtons(QMessageBox.StandardButton.Close)
        self.setInformativeText('<br>The Manual for this software can be found by clicking the help button or by '
                                'visiting <a href="https://github.com/Mission-DMX/Docs/blob/main/Editor/Readme.md">'
                                'the online manual</a>.<br>Copyright (c) the MissionDMX contributors')
        self.setDetailedText(CONTRIBUTORS_STR)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setTextFormat(Qt.RichText)
