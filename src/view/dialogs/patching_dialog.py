# coding=utf-8
""" Dialog for Patching Fixture"""
from PySide6 import QtWidgets

from ofl.fixture import Fixture, load_fixture, make_used_fixture, UsedFixture


class PatchingDialog(QtWidgets.QDialog):
    """ Dialog for Patching Fixture """

    def __init__(self, fixture: tuple[Fixture, int] = None, parent: object = None) -> None:
        super().__init__(parent)
        # Create widgets
        layout_fixture = QtWidgets.QHBoxLayout()
        self._fixture_name = QtWidgets.QLabel("no fixture" if fixture is None else fixture[0]['name'])
        self._select_mode = QtWidgets.QComboBox()
        layout_fixture.addWidget(self._fixture_name)
        layout_fixture.addWidget(self._select_mode)
        if fixture is None:
            self._select_fixture_button = QtWidgets.QPushButton(self)
            self._select_fixture_button.setText("select Fixture")
            self._select_fixture_button.clicked.connect(self.select_fixture)
            self._fixture: Fixture | None = None
            layout_fixture.addWidget(self._select_fixture_button)
        else:
            self._fixture: Fixture | None = fixture[0]
            for mode in self._fixture['modes']:
                self._select_mode.addItem(mode['name'])
            self._select_mode.setCurrentIndex(fixture[1])
        patching_layout = QtWidgets.QHBoxLayout()
        self._patching_node = QtWidgets.QLabel("Enter number of heads@uni-chanel/offset")
        self.patching = QtWidgets.QLineEdit("")
        patching_layout.addWidget(self._patching_node)
        patching_layout.addWidget(self.patching)

        layout_exit = QtWidgets.QHBoxLayout()
        self._ok = QtWidgets.QPushButton()
        self._ok.setText("patch")
        self._cancel = QtWidgets.QPushButton()
        self._cancel.setText("cancel")
        layout_exit.addWidget(self._cancel)
        layout_exit.addWidget(self._ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_fixture)
        layout.addLayout(patching_layout)
        layout.addLayout(layout_exit)

        # TODO Hier sollte noch ein nummernblock hin
        self.setLayout(layout)
        self._ok.clicked.connect(self.ok)
        self._cancel.clicked.connect(self.cancel)

    def get_used_fixture(self) -> UsedFixture:
        """property of the used Fixture"""
        return make_used_fixture(self._fixture, self._select_mode.currentIndex())

    def select_fixture(self) -> None:
        """select Fixture from File"""
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "select Fixture File", "",
                                                             "json Files (*.json);;All Files (*)", )
        if file_name:
            self._fixture = load_fixture(file_name)
            self._fixture_name.setText(self._fixture['name'])
            self._select_mode.clear()
            for mode in self._fixture['modes']:
                self._select_mode.addItem(mode['name'])

    def ok(self) -> None:
        """accept the Fixture"""
        self.accept()

    def cancel(self) -> None:
        """cancel Patching"""
        self.reject()
