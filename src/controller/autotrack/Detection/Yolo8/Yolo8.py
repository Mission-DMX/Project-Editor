import time
import cv2
import numpy as np
from controller.autotrack.Detection.Detector import Detector
import logging

class Yolo8(Detector):
    """
    The `Yolo8` class is a detector that uses the YOLOv8 model for object detection.

    Attributes:
        model (cv2.dnn.Net): The YOLOv8 model.

    Methods:
        - `__init__()`: Initialize the Yolo8 object.
        - `detect(frame)`: Detect objects in a given frame.
        - `loadModel()`: Load the YOLOv8 model from the ONNX file.
    """

    def __init__(self):
        """
        Initialize the Yolo8 object.
        """
        self.model: cv2.dnn.Net = None

    def detect(self, frame):
        """
        Detect objects in a given frame.

        Args:
            frame (numpy.ndarray): Input image frame.

        Returns:
            numpy.ndarray: Detected objects in the frame.
        """
        if self.model is None:
            self.loadModel()
        img = self.square_image(frame)
        self.model.setInput(img)
        start_time = time.time()
        outputs = self.model.forward()
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.getLogger().log(
            logging.DEBUG, f"Yolo8: Elapsed time: {elapsed_time} seconds"
        )
        outputs = np.array([cv2.transpose(outputs[0])])
        return outputs

    def loadModel(self):
        """
        Load the Yolo8 model from the ONNX file.
        """
        self.model = cv2.dnn.readNetFromONNX("./Detection/Yolo8/models/yolov8n.onnx")