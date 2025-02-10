# coding=utf-8
import cv2

from controller.autotrack.Sources.Loader import Loader


# TODO: Add caching for Frames again -> probably 10 frames
def print_supported_properties(cap):
    supported_property_names = [
        "CAP_PROP_POS_MSEC",
        "CAP_PROP_POS_FRAMES",
        "CAP_PROP_POS_AVI_RATIO",
        "CAP_PROP_FRAME_WIDTH",
        "CAP_PROP_FRAME_HEIGHT",
        "CAP_PROP_FPS",
        "CAP_PROP_FOURCC",
        "CAP_PROP_FRAME_COUNT",
        "CAP_PROP_FORMAT",
        "CAP_PROP_MODE",
        "CAP_PROP_BRIGHTNESS",
        "CAP_PROP_CONTRAST",
        "CAP_PROP_SATURATION",
        "CAP_PROP_HUE",
        "CAP_PROP_GAIN",
        "CAP_PROP_EXPOSURE",
        "CAP_PROP_CONVERT_RGB",
        "CAP_PROP_WHITE_BALANCE_BLUE_U",
        "CAP_PROP_RECTIFICATION",
        "CAP_PROP_MONOCHROME",
        "CAP_PROP_SHARPNESS",
        "CAP_PROP_AUTO_EXPOSURE",
        "CAP_PROP_GAMMA",
        "CAP_PROP_TEMPERATURE",
        "CAP_PROP_TRIGGER",
        "CAP_PROP_TRIGGER_DELAY",
        "CAP_PROP_WHITE_BALANCE_RED_V",
        "CAP_PROP_ZOOM",
        "CAP_PROP_FOCUS",
        "CAP_PROP_GUID",
        "CAP_PROP_ISO_SPEED",
        "CAP_PROP_BACKLIGHT",
        "CAP_PROP_PAN",
        "CAP_PROP_TILT",
        "CAP_PROP_ROLL",
        "CAP_PROP_IRIS",
        "CAP_PROP_SETTINGS",
        "CAP_PROP_BUFFERSIZE",
        "CAP_PROP_AUTOFOCUS",
        "CAP_PROP_SAR_NUM",
        "CAP_PROP_SAR_DEN",
        "CAP_PROP_BACKEND",
        "CAP_PROP_CHANNEL",
        "CAP_PROP_AUTO_WB",
        "CAP_PROP_WB_TEMPERATURE",
        "CAP_PROP_CODEC_PIXEL_FORMAT",
        "CAP_PROP_BITRATE",
        "CAP_PROP_ORIENTATION_META",
        "CAP_PROP_ORIENTATION_AUTO",
        "CAP_PROP_HW_ACCELERATION",
        "CAP_PROP_HW_DEVICE",
        "CAP_PROP_HW_ACCELERATION_USE_OPENCL",
        "CAP_PROP_OPEN_TIMEOUT_MSEC",
        "CAP_PROP_READ_TIMEOUT_MSEC",
        "CAP_PROP_STREAM_OPEN_TIME_USEC",
        "CAP_PROP_VIDEO_TOTAL_CHANNELS",
        "CAP_PROP_VIDEO_STREAM",
        "CAP_PROP_AUDIO_STREAM",
        "CAP_PROP_AUDIO_POS",
        "CAP_PROP_AUDIO_SHIFT_NSEC",
        "CAP_PROP_AUDIO_DATA_DEPTH",
        "CAP_PROP_AUDIO_SAMPLES_PER_SECOND",
        "CAP_PROP_AUDIO_BASE_INDEX",
        "CAP_PROP_AUDIO_TOTAL_CHANNELS",
        "CAP_PROP_AUDIO_TOTAL_STREAMS",
        "CAP_PROP_AUDIO_SYNCHRONIZE",
        "CAP_PROP_LRF_HAS_KEY_FRAME",
        "CAP_PROP_CODEC_EXTRADATA_INDEX",
        "CAP_PROP_FRAME_TYPE",
        "CAP_PROP_N_THREADS",
    ]

    # Get the supported properties and their current values
    supported_properties = {}
    for (
        prop_name
    ) in supported_property_names:  # Range of property IDs, you can adjust as needed
        prop_id = getattr(cv2, prop_name, -1)  # Get the property ID by name
        prop_value = cap.get(prop_id)
        if prop_value != -1.0:  # Check if the property is supported
            supported_properties[prop_id] = prop_value
    for prop_id, prop_value in supported_properties.items():
        print(
            f"Property ID {prop_id} ({supported_property_names[prop_id]}): {prop_value}"
        )


class CameraLoader(Loader):
    """
    The `CameraLoader` class is used for capturing frames from a camera device.

    Attributes:
        - cap (cv2.VideoCapture): The OpenCV VideoCapture object for accessing the camera.

    Methods:
        - get_last(ms: int): Get the last captured frame from the camera.

    Args:
        - device_path (str): The path or identifier of the camera device to capture frames from.
    """

    def get_last(self, ms: int):
        """
        Get the last captured frame from the camera.

        Args:
            ms (int): Not used in this implementation. It's included for compatibility with the Loader interface.

        Returns:
            numpy.ndarray: The last captured frame from the camera.

        Note:
            This method captures the most recent frame from the camera device.

        Raises:
            Exception: If capturing a frame from the camera fails.
        """
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to capture frame from the camera.")
        return frame

    def __init__(self, device_path):
        """
        Initialize the CameraLoader with the specified camera device.

        Args:
            device_path (str): The path or identifier of the camera device to capture frames from.

        Note:
            This constructor sets up the camera capture using OpenCV's VideoCapture.
        """
        self.cap = cv2.VideoCapture(device_path, cv2.CAP_DSHOW)
        print_supported_properties(self.cap)
        self.cap.set(cv2.CAP_PROP_FPS, 60.0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M','J','P','G'))
        #self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('Y','U','Y','V'))
        """
        # Print the supported properties and their values


        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 200)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # turn the autofocus off
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)


        self.cap.set(cv2.CAP_PROP_ISO_SPEED, 2000)  # Example: Set ISO to 800
        self.cap.set(
            cv2.CAP_PROP_WB_TEMPERATURE, 4200
        )  # Set manual white balance temperature to 4200K
"""
