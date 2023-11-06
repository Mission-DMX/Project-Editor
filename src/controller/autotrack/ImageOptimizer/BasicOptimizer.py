import cv2

from ImageOptimizer.Optimizer import Optimizer


class ResizeOptimizer(Optimizer):
    """
    The `ResizeOptimizer` class resizes an image to a specified size.

    Args:
        name (str): The name of the optimizer.
        size (tuple): A tuple representing the target size (width, height).

    Methods:
        - `process(image)`: Resize the input image to the specified size.

    Inherits from:
        - `Optimizer`
    """

    def __init__(self, name, size):
        super().__init__(name)
        self.size = size

    def process(self, image):
        """
        Resize the input image to the specified size.

        Args:
            image (numpy.ndarray): The input image.

        Returns:
            numpy.ndarray: The resized image.
        """
        return cv2.resize(image, self.size)


class CropOptimizer(Optimizer):
    """
    The `CropOptimizer` class crops an image based on provided dimensions.

    Args:
        name (str): The name of the optimizer.
        dimensions (tuple): A tuple representing the crop dimensions (x1, x2, y1, y2).

    Methods:
        - `process(image)`: Crop the input image based on the provided dimensions.

    Inherits from:
        - `Optimizer`
    """

    def __init__(self, name, dimensions):
        super().__init__(name)
        self.dimensions = dimensions

    def process(self, image):
        """
        Crop the input image based on the provided dimensions.

        Args:
            image (numpy.ndarray): The input image.

        Returns:
            numpy.ndarray: The cropped image.
        """
        image = image[
            self.dimensions[0] : self.dimensions[1],
            self.dimensions[2] : self.dimensions[3],
        ]
        return image


class GrayScaleOptimizer(Optimizer):
    """
    The `GrayScaleOptimizer` class converts an image to grayscale.

    Args:
        name (str): The name of the optimizer.

    Methods:
        - `process(image)`: Convert the input image to grayscale.

    Inherits from:
        - `Optimizer`
    """

    def __init__(self, name):
        super().__init__(name)

    def process(self, image):
        """
        Convert the input image to grayscale.

        Args:
            image (numpy.ndarray): The input image.

        Returns:
            numpy.ndarray: The grayscale image.
        """
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # This is needed to keep the image in 3 channels but grayscale
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image
