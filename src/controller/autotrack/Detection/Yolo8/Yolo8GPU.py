# coding=utf-8
import logging
import os
import time

import cv2
import numpy as np
import onnxruntime as rt

from controller.autotrack.Detection.Detector import Detector
from utility import resource_path


class Yolo8GPU(Detector):
    """
    The `Yolo8` class is a detector that uses the YOLOv8 cues for object detection.

    Attributes:
        model (cv2.dnn.Net): The YOLOv8 cues.

    Methods:
        - `__init__()`: Initialize the Yolo8 object.
        - `detect(frame)`: Detect objects in a given frame.
        - `loadModel()`: Load the YOLOv8 cues from the ONNX file.
    """

    def __init__(self):
        """
        Initialize the Yolo8 object.
        """
        self.model = None

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
        input_name = self.model.get_inputs()[0].name
        # Perform inference on the GPU
        # inputs = {self.cues.get_inputs()[0].name: img}
        start_time = time.time()
        results = self.model.run(None, {"images": img})

        output0 = results[0]
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.getLogger().log(
            logging.DEBUG, f"Yolo8: Elapsed time: {elapsed_time} seconds"
        )
        # outputs = np.array([cv2.transpose(outputs[0])])
        outputs2 = np.array([cv2.transpose(output0[0])])
        return output0[0]

    def loadModel(self):
        """
        Load the Yolo8 cues from the ONNX file.
        """
        # self.cues = cv2.dnn.readNetFromONNX("./Detection/Yolo8/models/yolov8n.onnx")
        self.model = rt.InferenceSession(
            resource_path(os.path.join("resources", "autotrack_models", "yolov8n.onnx")),
            providers=[
                "CUDAExecutionProvider",
                "MIGraphXExecutionProvider",
                "ROCMExecutionProvider",
                "OpenVINOExecutionProvider",
                "CPUExecutionProvider",
            ],
        )
