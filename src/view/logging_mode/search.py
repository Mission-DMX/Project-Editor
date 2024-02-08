# coding=utf-8
"""search in logging Items"""
import enum


class Operation(enum.Enum):
    """possible Operations"""
    AND = 1
    OR = 2


class Search:
    """search in logging Items"""

    def __init__(self, items: tuple[str, str], operation: Operation):
        self._ITEMS: tuple[str, str] = items
        self._OPERATION: Operation = operation

    @property
    def items(self) -> tuple[str, str]:
        """items in Search"""
        return self._ITEMS

    @property
    def operation(self) -> Operation:
        """operation"""
        return self._OPERATION
