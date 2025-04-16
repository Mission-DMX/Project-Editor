# coding=utf-8
from abc import ABC, abstractmethod

import cv2
import numpy as np


class Detector(ABC):
    """
    The `Detector` class is an abstract base class for object detection.


    Methods:
        - `detect(frame)`: Abstract method for detecting objects in a given frame.
        - `square_image(frame)`: Resize the input frame into a square image and prepare it for inference.

    Attributes:
        None
    """

    @abstractmethod
    def detect(self, frame):
        """
        Abstract method for detecting objects in a given frame.

        Args:
            frame (numpy.ndarray): Input image frame.

        Returns:
            numpy.ndarray: Detected objects in the frame.
        """
        pass

    def square_image(self, frame):
        """
        Resize the input frame into a square image and prepare it for inference.

        Args:
            frame (numpy.ndarray): Input image frame.

        Returns:
            numpy.ndarray: A preprocessed square image.
        """
        h, w, *_ = frame.shape

        # Prepare a square image for inference
        length = max(h, w)
        image = np.zeros((length, length, 3), np.uint8)
        image[0:h, 0:w] = frame

        # Calculate scale factor
        scale = length / 640

        # Preprocess the image and prepare blob for model
        blob = cv2.dnn.blobFromImage(
            image, scalefactor=1 / 255, size=(640, 640), swapRB=True
        )
        return blob
