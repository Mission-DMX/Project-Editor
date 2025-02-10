from PySide6 import QtWidgets
from PySide6.QtWidgets import QMainWindow, QVBoxLayout

from model.control_desk import *
from Style import Style
from view.show_mode.node_editor_widgets import ColumnSelect

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
    app.setApplicationName("mission-dmx-editor")
    app.setApplicationDisplayName("Mission DMX")
    app.setOrganizationName("missionDMX")
    app.setOrganizationDomain("technikradio.org")
    app.setDesktopSettingsAware(True)
    # app.setWindowIcon(QIcon("resources/app-icon.png"))
    window = QMainWindow()
    set_network_manager(NetworkManager(broadcaster=Broadcaster(), parent=window))
    for bs_desc in ["Test Set 1", "Test Set 2"]:
        bs = BankSet()
        bs.description = bs_desc
        for bank_index in range(4):
            bank = FaderBank()
            for col in range(8):
                if col % 2 == 0:
                    column = ColorDeskColumn()
                else:
                    column = RawDeskColumn()
                bank.add_column(column)
            bs.add_bank(bank)
        bs.link()
    layout = QVBoxLayout()
    select_widget = ColumnSelect(parent=window)
    select_widget.configuration = {}
    layout.addWidget(select_widget.get_widget())
    window.setLayout(layout)
    window.showMaximized()
    app.exec()
    print(select_widget.configuration)
