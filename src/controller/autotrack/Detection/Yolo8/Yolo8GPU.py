"""YOLOv8 models for object detection."""

import os
import time
from logging import getLogger
from typing import override

logger = getLogger(__name__)

import cv2
import numpy as np

_import_successful = False
try:
    import onnxruntime as rt
    _import_successful = True
except ImportError as e:
    logger.error("Failed to load onnxruntime: %s", e)

from controller.autotrack.Detection.Detector import Detector
from utility import resource_path




class Yolo8GPU(Detector):
    """Use YOLOv8 models for object detection.

    Attributes:
        model: The YOLOv8 model.

    Methods:
        __init__: Initialize the Yolo8 object.
        detect: Detect objects in a given frame.
        load_model: Load the YOLOv8 model from the ONNX file.

    """

    def __init__(self):
        """Initialize the Yolo8 object."""
        self.model = None

    @override
    def detect(self, frame):
        """Detect objects in a given frame.

        Args:
            frame: Input image frame.

        Returns:
            Detected objects in the frame.

        """
        if self.model is None:
            self.loadModel()
            return np.zeros(4)
        img = self.square_image(frame)
        input_name = self.model.get_inputs()[0].name
        # Perform inference on the GPU
        # inputs = {self.model.get_inputs()[0].name: img}
        start_time = time.time()
        results = self.model.run(None, {"images": img})

        output0 = results[0]
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.debug("Yolo8: Elapsed time: %s seconds", elapsed_time)
        # outputs = np.array([cv2.transpose(outputs[0])])
        outputs2 = np.array([cv2.transpose(output0[0])])
        return output0[0]

    def loadModel(self):
        """Load the Yolo8 models from the ONNX file."""
        if not _import_successful:
            logger.error("Failed to load model, as onnxruntime is not initialized.")
            return
        # self.model = cv2.dnn.readNetFromONNX("./Detection/Yolo8/models/yolov8n.onnx")
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
