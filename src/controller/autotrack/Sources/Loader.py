# coding=utf-8
"""defining data loader"""
from abc import ABC, abstractmethod


class Loader(ABC):
    """
    The `Loader` class is an abstract base class for defining data loaders.

    Methods:
        - `get_last(ms: int)`: Abstract method to retrieve the most recent data item.

    Attributes:
        This class has no specific attributes.

    Note:
        To create a custom data loader, inherit from this class and implement the `get_last` method.

    """

    @abstractmethod
    def get_last(self, ms: int):
        """
        Get the most recent data item.

        Args:
            ms (int): The timestamp in milliseconds (unused in some implementations).

        Returns:
            The most recent data item.

        Note:
            This method should be implemented by subclasses to retrieve the most recent data item.
        """
        pass
