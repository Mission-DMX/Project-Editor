from aiortc import VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from controller.autotrack.Sources.Loader import Loader


# TODO: aiortc for all Loaders
class WebRTCLoader(Loader):
    """
    The `WebRTCLoader` class is a data loader that retrieves video frames from a WebRTC source using the aiortc library.

    Attributes:
        player (MediaPlayer): The MediaPlayer instance used for retrieving video frames from the WebRTC source.

    Args:
        url (str): The URL of the WebRTC source.

    Note:
        Make sure to have the aiortc library installed to use this loader.

    """

    def get_last(self, ms: int):
        """
        Get the most recent video frame from the WebRTC source.

        Args:
            ms (int): The timestamp in milliseconds (unused).

        Returns:
            The most recent video frame.

        """
        return self.player.video.recv()

    def __init__(self, url):
        """
        Initialize a WebRTCLoader instance with the provided WebRTC source URL.

        Args:
            url (str): The URL of the WebRTC source.

        """
        self.player = MediaPlayer(url)
        super().__init__()
