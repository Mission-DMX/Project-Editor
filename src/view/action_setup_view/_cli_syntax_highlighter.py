"""Contains a syntax highlighter for our CLI language."""

import re
from typing import override

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QBrush, QColor, QFont, QSyntaxHighlighter, QTextCharFormat, QTextDocument


class CLISyntaxHighlighter(QSyntaxHighlighter):
    """Provides syntax highlighting for input CLI commands."""

    def __init__(self, document: QTextDocument | None = None) -> None:
        """Initialize the syntax highlighter."""
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

        self._escape_format = QTextCharFormat()
        self._escape_format.setForeground(QBrush(QColor.fromRgb(0xFF, 0xA5, 0)))
        self._escape_expression = QRegularExpression('\\\\[tnr$"]')
        self._mappings[self._escape_expression] = self._escape_format

        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QBrush(QColor.fromRgb(0, 125, 0)))
        self._comment_expression = QRegularExpression("(#.+)|#")
        self._mappings[self._comment_expression] = self._comment_format

        self._variable_format = QTextCharFormat()
        self._variable_format.setForeground(QBrush(QColor.fromRgb(0, 80, 80)))
        self._variable_expression = QRegularExpression("(?<=[^\\\\])(\\$\\w+)")
        self._mappings[self._variable_expression] = self._variable_format

    @override
    def highlightBlock(self, text: str, /) -> None:
        """Highlight text blocks.

        This method gets called for every text block. It sets the formats on it.

        :param text: The text to inspect.
        """
        for pattern, fmt in self._mappings.items():
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
