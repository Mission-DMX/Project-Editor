# coding=utf-8
from abc import ABC, abstractmethod


class Optimizer(ABC):
    """
    The `Optimizer` class is an abstract base class for implementing image optimization steps.

    Attributes:
        name (str): The name or identifier for the optimization step.

    Methods:
        - `process(image)`: Abstract method to perform the image optimization.

    """

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def process(self, image):
        """
        Abstract method to perform the image optimization.

        Args:
            image (numpy.ndarray): The input image to be optimized.

        Returns:
            numpy.ndarray: The optimized image.
        """
        pass
