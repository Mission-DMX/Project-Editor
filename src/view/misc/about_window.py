from logging import getLogger

from PySide6.QtWidgets import QMessageBox


logger = getLogger(__file__)


def read_entire_file_as_str(file_path: str) -> str:
    try:
        with open(file_path, 'r') as f:
            text = f.read()
    except IOError as e:
        text = "Unknown Debug"
        logger.error("Unable to load file string from {}.".format(file_path), e)
    return text


VERSION_STR = read_entire_file_as_str("resources/version.txt")
CONTRIBUTORS_STR = read_entire_file_as_str("resources/contributors.html")


class AboutWindow(QMessageBox):
    def __init__(self, parent):
        super().__init__(title="About", parent=parent)
        self.setIcon(QMessageBox.Icon.Information)
        self.setStandardButtons(QMessageBox.StandardButton.Close)
        self.setText("MissionDMX - Version {}".format(VERSION_STR))
        self.setInformativeText("Copyright (c) the MissionDMX contributors")
        self.setDetailedText(CONTRIBUTORS_STR)
