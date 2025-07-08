
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument


class CLISyntaxHighlighter(QSyntaxHighlighter):
    """
    This class provides syntax highlighting for input CLI commands.
    """
    def __init__(self, document: QTextDocument | None = None):
        super().__init__(document)
        self._mappings = {}
        self._space_format = QTextCharFormat()
        self._space_format.setFontWeight(QFont.Weight.Bold)
        self._space_expression = QRegularExpression("\\s")
        self._mappings[self._space_expression] = self._space_format

        self._number_format = QTextCharFormat()
        self._number_format.setForeground(QBrush(QColor.fromRgb(0xFF, 0xA5, 0)))
        self._number_expression = QRegularExpression("\\d+")
        self._mappings[self._number_expression] = self._number_format

        self._string_format = QTextCharFormat()
        self._string_format.setForeground(QBrush(QColor.fromRgb(0, 0, 0xFF)))
        self._string_expression = QRegularExpression('\\".+\\"')
        self._mappings[self._string_expression] = self._string_format

        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QBrush(QColor.fromRgb(0, 125, 0)))
        self._comment_expression = QRegularExpression("(#.+)|#")
        self._mappings[self._comment_expression] = self._comment_format

    def highlightBlock(self, text, /) -> None:
        """This method gets called for every text block. It sets the formats on it"""
        for pattern, fmt in self._mappings.items():
            iter = pattern.globalMatch(text)
            while iter.hasNext():
                match = iter.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
