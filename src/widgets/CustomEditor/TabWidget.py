from PySide6 import QtWidgets

from src.DMXModel import Universe, Channel
from src.widgets.CustomEditor.Dialog import CustomEditorDialog


class CustomEditorTabWidget(QtWidgets.QWidget):
    """Widget for group of channels for CustomEditorWidget.

    Can contain 0 (default) to 16 ChannelWidgets to control up to 16 specific channels.
    Channels can be named and removed.
    """

    def __init__(self, universes: list[Universe], parent=None):
        """Inits the custom editor tab.

        Args:
            universes: list of universes which channels can be registered in this editor tab.
            parent: Qt parent of the widget.
        """

        super().__init__(parent=parent)

        self.testInt = 0

#        self._channel_widgets: list[ChannelWidget] = []
        self._universes: list[Universe] = universes
        self.setFixedSize(752, 810)

        self._layout: QtWidgets.QGridLayout = QtWidgets.QGridLayout(self)
        self._layout.setColumnStretch(0, 400)
        self._layout.setColumnStretch(1, 30)
        self._layout.setColumnStretch(2, 400)
        for i in range(18):
            self._layout.setRowStretch(i, 30)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setVerticalSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)

        self._add_button = QtWidgets.QPushButton("+", self)
        self._add_button.setFixedSize(376, 30)
        self._add_button.clicked.connect(self._show_dialog)

        self._layout.addWidget(self._add_button, 0, 0, 1, 1)

        self.setLayout(self._layout)

    def _show_dialog(self) -> None:
        """Shows a dialog to add a new ChannelWidget."""
#        if len(self._channel_widgets) >= 16:
#            return

        dlg = CustomEditorDialog()

        if dlg.exec():
            u_id, address, description = dlg.get_inputs()
            description = description if description != "" else f"Universe {u_id + 1} Channel {address + 1}"
            self._add_channel(self._universes[u_id].channels[address], description)

    def _add_channel(self, channel: Channel, description: str) -> None:
        """Adds the channel_widget to the tab.

        The ChannelWidget is added at the bottom of the list.
        The add button is moved one row down.
        """
#        channel_widget = ChannelWidget(channel, draw_horizontally=True, parent=self)
#        self._channel_widgets.append(channel_widget)

        label = QtWidgets.QLabel(description, parent=self)
        label.setFixedSize(376, 30)
        del_button = QtWidgets.QPushButton("X", parent=self)
        del_button.setFixedSize(30, 30)
#        del_button.clicked.connect(lambda: self._del_channel(channel_widget, del_button, label))

        self._layout.removeWidget(self._add_button)

        new_widget_row = len(self._channel_widgets) - 1

#        self._layout.addWidget(channel_widget, new_widget_row, 0, 1, 1)
        self._layout.addWidget(del_button, new_widget_row, 1, 1, 1)
        self._layout.addWidget(label, new_widget_row, 2, 1, 1)
        self._layout.addWidget(self._add_button, new_widget_row + 1, 0, 1, 1)

#    def _del_channel(self, channel_widget: ChannelWidget, del_button: QtWidgets.QPushButton, label: QtWidgets.QLabel) -> None:
#        """Removes channel_widget from the tab.

#        The ChannelWidget is removed from the layout and deleted.
#        The add button and all ChannelWidgets below it are moved up one row.
#        """
#        cw_row = self._channel_widgets.index(channel_widget)

#        self._channel_widgets.remove(channel_widget)

#        """TODO DELETE"""
#        delete_widget(channel_widget, self._layout)
#        delete_widget(del_button, self._layout)
#        delete_widget(label, self._layout)

#        for new_row in range(cw_row, len(self._channel_widgets)):
#            c_widget = self._layout.itemAtPosition(new_row + 1, 0).widget()
#            c_button = self._layout.itemAtPosition(new_row + 1, 1).widget()
#            c_label = self._layout.itemAtPosition(new_row + 1, 2).widget()

#            self._layout.removeWidget(c_widget)
#            self._layout.removeWidget(c_button)
#            self._layout.removeWidget(c_label)

#            self._layout.addWidget(c_widget, new_row, 0, 1, 1)
#            self._layout.addWidget(c_button, new_row, 1, 1, 1)
#            self._layout.addWidget(c_label, new_row, 2, 1, 1)

#        self._layout.removeWidget(self._add_button)
#        self._layout.addWidget(self._add_button, len(self._channel_widgets), 0, 1, 1)

