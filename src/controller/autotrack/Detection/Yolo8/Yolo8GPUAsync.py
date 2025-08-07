"""YOLOv8 models for object detection."""

import threading
import time
from logging import getLogger

import cv2
import numpy
import numpy as np
import onnxruntime as rt
from Detection.Detector import Detector

logger = getLogger(__name__)


class Yolo8GPUAsync(Detector):
    """Use YOLOv8 models for object detection.

    Attributes:
        model: The YOLOv8 model.

    """

    def __init__(self):
        """Initialize the Yolo8 object."""
        self.model = rt.InferenceSession("./Detection/Yolo8/models/yolov8n.onnx")
        self.lock = threading.Lock()  # Lock to protect access to the model

    def detect(self, frame: numpy.ndarray):
        """Detect objects in a given frame.

        Args:
            frame: Input image frame.

        Returns:
            Detected objects in the frame.

        """
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

    async def run_inference(self, img):
        """Run inference on the given image using the loaded model.

        Args:
            img: Input image tensor or array.

        Returns:
            The raw inference results returned by the model.

        """
        with self.lock:
            results = self.model.run(None, {"images": img})
            # Process the inference results here
            return results

    def loadModel(self):
        """Load the Yolo8 model from the ONNX file."""
        # self.model = cv2.dnn.readNetFromONNX("./Detection/Yolo8/models/yolov8n.onnx")
        pass
