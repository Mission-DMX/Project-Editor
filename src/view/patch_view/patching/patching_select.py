"""select Manufacturer"""
import os
import zipfile
from logging import getLogger

import requests
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget

import style
from layouts.flow_layout import FlowLayout
from model import BoardConfiguration
from model.ofl.fixture import Fixture
from model.ofl.manufacture import Manufacture, generate_manufacturers
from view.dialogs.patching_dialog import PatchingDialog
from view.patch_view.patching.fixture_item import FixtureItem
from view.patch_view.patching.manufacturer_item import ManufacturerItem
from view.patch_view.patching.mode_item import ModeItem

logger = getLogger(__name__)


class PatchingSelect(QtWidgets.QScrollArea):
    """select Manufacturer"""

    def __init__(self, board_configuration: BoardConfiguration, parent: QWidget) -> None:
        super().__init__(parent)
        self._board_configuration = board_configuration
        cache_path = "/var/cache/missionDMX"
        if not os.path.exists(cache_path):
            os.mkdir(cache_path)
        fixtures_path = os.path.join(cache_path, "fixtures/")
        zip_path = os.path.join(cache_path, "fixtures.zip")
        if not os.path.exists(fixtures_path):
            logger.info("Downloading fixture library. Please wait")
            url = "https://open-fixture-library.org/download.ofl"
            r = requests.get(url, allow_redirects=True, timeout=5)
            if r.status_code != 200:
                logger.error("Failed to download fixture library")
                return

            with open(zip_path, "wb") as file:
                file.write(r.content)
            with zipfile.ZipFile(zip_path) as zip_ref:
                zip_ref.extractall(fixtures_path)
            logger.info("Fixture lib downloaded and installed.")
        manufacturers: list[tuple[Manufacture, list[Fixture]]] = generate_manufacturers(fixtures_path)
        self.index = 0
        self.container = QtWidgets.QStackedWidget()
        manufacturers_layout = FlowLayout()
        for manufacturer in manufacturers:
            manufacturers_layout.addWidget(self._generate_manufacturer_item(manufacturer))

        manufacturers_widget = QtWidgets.QWidget()
        manufacturers_widget.setLayout(manufacturers_layout)
        self.container.addWidget(manufacturers_widget)

        self.setWidgetResizable(True)
        self.setWidget(self.container)
        self.container.setCurrentIndex(self.container.count() - 1)

    def _generate_manufacturer_item(self, manufacturer: tuple[Manufacture, list[Fixture]]) -> ManufacturerItem:
        manufacturer_layout = FlowLayout()
        reset_button = QtWidgets.QPushButton("...")
        reset_button.setFixedSize(150, 100)
        reset_button.setStyleSheet(style.PATCH + "background-color: white;")
        reset_button.clicked.connect(self.reset)
        manufacturer_layout.addWidget(reset_button)
        for fixture in manufacturer[1]:
            manufacturer_layout.addWidget(self._generate_fixture_item(fixture))

        manufacturer_widget = QtWidgets.QWidget()
        manufacturer_widget.setLayout(manufacturer_layout)
        self.container.addWidget(manufacturer_widget)
        item = ManufacturerItem(manufacturer[0])
        item.clicked.connect(lambda _, _index=self.index: self.select_fixture(_index))
        self.index += 1

        return item

    def _generate_fixture_item(self, fixture: Fixture) -> FixtureItem:
        fixture_layout = FlowLayout()
        reset_button = QtWidgets.QPushButton("...")
        reset_button.setFixedSize(150, 100)
        reset_button.setStyleSheet(style.PATCH + "background-color: white;")
        reset_button.clicked.connect(self.reset)
        fixture_layout.addWidget(reset_button)
        for index, mode in enumerate(fixture["modes"]):
            mode_item = ModeItem(mode)
            mode_item.clicked.connect(lambda _, _fixture=fixture, _index=index: self._run_patch(_fixture, _index))
            fixture_layout.addWidget(mode_item)

        fixture_widget = QtWidgets.QWidget()
        fixture_widget.setLayout(fixture_layout)
        self.container.addWidget(fixture_widget)
        fixture_item = FixtureItem(fixture)
        fixture_item.clicked.connect(lambda _, _index=self.index: self.select_fixture(_index))
        self.index += 1
        return fixture_item

    def select_fixture(self, index: int) -> None:
        """select_fixture"""
        self.container.setCurrentIndex(index)

    def reset(self) -> None:
        """reset to start"""
        self.container.setCurrentIndex(self.container.count() - 1)

    def _run_patch(self, fixture: Fixture, index: int) -> None:
        """run the patching dialog"""
        dialog = PatchingDialog(self._board_configuration, (fixture, index))
        dialog.finished.connect(lambda: self._patch(dialog))

        dialog.open()

    def _patch(self, form: PatchingDialog) -> None:
        """
            patch fixtures from PatchingDialog
        """
        if form.result():
            form.generate_fixtures()
        self._board_configuration.broadcaster.view_leave_patching.emit()
