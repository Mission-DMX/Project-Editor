# coding=utf-8
"""Dialogs to display fish exceptions"""

from PySide6 import QtWidgets, QtGui

error_dict: dict[str, str] = {"E001": "Fish Error: Filter not implemented in Allocation",
                              "E002": "Fish Error: Filter not implemented in Construction",
                              "E003": "Fish Error: Filter configuration exception",
                              "E004": "Fish Error: Filter scheduling exception",
                              "E005": "Fish Error: Cyclic or broken dependency while scheduling",
                              "E006": "Fish Error: Unknown requested output channel"
                              }


class FishExceptionsDialog(QtWidgets.QDialog):
    """"Dialog to display fish exceptions"""
    _open_dialogs: list[QtWidgets.QDialog] = []

    def __init__(self, log: str, reason: str, cause: str, parent=None):
        super().__init__()
        self.setWindowTitle("Fish Error")
        layout = QtWidgets.QHBoxLayout(self)
        da = HoverTextBrowser(f"""Log:<br>{log}</p>"""
                              f"""<p>Reason:<br>{reason}</p>"""
                              f"<p>Cause:<br>{cause}")
        layout.addWidget(da)
        self.setLayout(layout)

    def open(self):
        """Opens dialog and automatically keeps it open"""
        self._open_dialogs.append(self)
        self.finished.connect(lambda: self._open_dialogs.remove(self))
        super().open()


class HoverTextBrowser(QtWidgets.QTextBrowser):
    """Text Browser with tooltip"""

    def __init__(self, text: str):
        super().__init__()
        self.setMouseTracking(True)
        self.setHtml("""<p>""" + text + """</p>""")
        self.highlight_words()

    def highlight_words(self):
        """Highlights words in text"""
        cursor = self.textCursor()
        document_text = self.toPlainText()

        for word in error_dict.keys():
            start_pos = 0
            while True:
                start_pos = document_text.find(word, start_pos)
                if start_pos == -1:
                    break
                cursor.setPosition(start_pos)
                cursor.movePosition(QtGui.QTextCursor.MoveOperation.Right, QtGui.QTextCursor.MoveMode.KeepAnchor,
                                    len(word))
                text_format = QtGui.QTextCharFormat()
                text_format.setForeground(QtGui.QColor("blue"))
                text_format.setFontUnderline(True)
                cursor.setCharFormat(text_format)
                start_pos += len(word)

    def mouseMoveEvent(self, event):
        """mouse Event for Hover tooltip"""
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        hovered_text = cursor.selectedText()

        if hovered_text in error_dict:
            QtWidgets.QToolTip.showText(event.globalPosition().toPoint(), error_dict[hovered_text], self)
        else:
            QtWidgets.QToolTip.hideText()

        super().mouseMoveEvent(event)
