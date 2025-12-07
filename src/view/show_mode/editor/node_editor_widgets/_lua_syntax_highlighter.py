from __future__ import annotations

from typing import TYPE_CHECKING, override

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QSyntaxHighlighter, Qt, QTextCharFormat

if TYPE_CHECKING:
    from PySide6.QtGui import QTextDocument


class LuaSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument | None = None) -> None:
        super().__init__(document)
        rules = [
            (
                r"\b(and|break|do|else|elseif|end|for|function|if|in|local|repeat|return|then|until|while)\b",
                Qt.GlobalColor.green, False, False
            ),
            (r"\b\d+\.?\d*\b", Qt.GlobalColor.cyan, False, False),  # Numbers
            (r"\b(math\.maxinteger|nil)\b", Qt.GlobalColor.cyan, False, False),  # Built in values
            (r'\".*?\"|\'[^\']*\'', Qt.GlobalColor.darkYellow, False, False),  # Strings
            (r"--\[\[", Qt.GlobalColor.darkGray, True, False), # multi line comments start
            (r"--\]\]", Qt.GlobalColor.darkGray, False, True),
            (r"--.*", Qt.GlobalColor.darkGray, False, False),  # Single line comments
        ]
        self._formatting = []
        for pattern, color, em, dm in rules:
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._formatting.append((QRegularExpression(pattern), fmt, em, dm))
        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(Qt.GlobalColor.darkGray)

    @override
    def highlightBlock(self, text: str) -> None:
        in_comment = self.previousBlockState() == 1
        if in_comment:
            start = 0
            length = len(text)
            self.setCurrentBlockState(1)
            self.setFormat(start, length, self._comment_format)
        for pattern, fmt, enables_multiline_comment, disables_multiline_comment in self._formatting:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                if enables_multiline_comment:
                    if self.currentBlockState() == 0:
                        self._reformat()
                    self.setCurrentBlockState(1)
                if disables_multiline_comment:
                    if self.currentBlockState() == 1 or self.previousBlockState() == 1:
                        self._reformat()
                    self.setCurrentBlockState(0)
                formatting_allowed = not in_comment or enables_multiline_comment or disables_multiline_comment
                if formatting_allowed:
                    self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

    def _reformat(self) -> None:
        self.document().markContentsDirty(0, self.document().characterCount())
