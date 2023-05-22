from PySide6 import QtWidgets
from PySide6.QtWidgets import QMainWindow, QBoxLayout

from Style import Style
from model.broadcaster import Broadcaster
from model.control_desk import *
from network import NetworkManager
from view.filter_mode.node_editor_widgets.column_select import ColumnSelect

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setStyleSheet(Style.APP)
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
    layout = QBoxLayout()
    select_widget = ColumnSelect()
    layout.addWidget(select_widget)
    window.layout(layout)
    window.showMaximized()
    app.exec()
    print(select_widget.configuration)
