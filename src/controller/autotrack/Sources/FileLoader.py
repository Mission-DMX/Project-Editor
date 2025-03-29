# coding=utf-8
import os
import time

import cv2

from controller.autotrack.Sources.Loader import Loader


class FileLoader(Loader):
    """
    The `FileLoader` class is used for loading video files and retrieving frames from them.

    Attributes:
        - filePath (str): The path to the video file.
        - video (cv2.VideoCapture): The OpenCV VideoCapture object for reading the video.
        - start_time (int): The start time in milliseconds when the video was loaded.
        - loop (bool): Indicates whether the video should loop when it reaches the end.

    Methods:
        - get_last(ms=-1): Get the frame at the specified time in milliseconds.
        - load_file(path): Load a video file from the given path.
        - simulated_time(): Calculate the simulated time elapsed since video loading.
    """

    filePath: str
    video: cv2.VideoCapture
    start_time: int

    def __init__(self, loop=False):
        """
        Initialize the FileLoader.

        Args:
            loop (bool): Indicates whether the video should loop when it reaches the end.
        """
        self.loop = loop

    def get_last(self, ms: int = -1):
        """
        Get the frame at the specified time in milliseconds.

        Args:
            ms (int): The time in milliseconds to seek to in the video. Default is -1, which uses simulated time.

        Returns:
            numpy.ndarray: The frame at the specified time.

        Raises:
            Exception: If the video cannot be read or if no frame is available.
        """
        if ms == -1:
            ms = self.simulated_time()
        if not self.video.isOpened():
            raise Exception(f"The video '{self.filePath}' couldn't be read.")
        self.video.set(cv2.CAP_PROP_POS_MSEC, ms)
        ret, frame = self.video.read()
        if not ret:
            if self.loop:
                self.start_time = int(time.time() * 1000)
            else:
                raise Exception(f"No frame after {ms} milliseconds.")
        return frame

    def load_file(self, path: str):
        """
        Load a video file from the given path.

        Args:
            path (str): The path to the video file.

        Raises:
            FileNotFoundError: If the specified file doesn't exist.
            Exception: If the video cannot be read.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"The file '{path}' doesn't exist.")
        self.filePath = path
        video_capture = cv2.VideoCapture(path)
        if not video_capture.isOpened():
            raise Exception(f"The video '{self.filePath}' couldn't be read.")
        self.video = video_capture
        self.start_time = int(time.time() * 1000)

    def simulated_time(self) -> int:
        """
        Calculate the simulated time elapsed since video loading.

        Returns:
            int: The simulated time in milliseconds.
        """
        return int(time.time() * 1000) - self.start_time
