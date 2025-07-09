"""search in logging Items"""
import enum


class Operation(enum.Enum):
    """possible Operations"""
    IS = 0
    AND = 1
    OR = 2


class Search:
    """search in logging Items"""

    def __init__(self, items: tuple[str, str], operation: Operation) -> None:
        self._items: tuple[str, str] = items
        self._operation: Operation = operation

    @property
    def items(self) -> tuple[str, str]:
        """items in Search"""
        return self._items

    @property
    def operation(self) -> Operation:
        """operation"""
        return self._operation
