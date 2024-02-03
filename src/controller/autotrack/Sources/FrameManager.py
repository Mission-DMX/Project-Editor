import numpy as np
from PySide6.QtCore import Slot, QThread, Signal


class FrameManager(QThread):
    frame_captured = Signal(np.ndarray, name="frame")

    def __init__(self):
        super().__init__()
        self.loader = None

    @Slot()
    def run(self):
        while True:
            if self.loader is not None:
                frame = self.loader.get_last(-1)
                frames = []

                if frame is not None:
                    frames.append(frame)

                    if len(frames) > 10:
                        frames.pop(0)
                    output = frames[-1]
                    self.frame_captured.emit(output)

    def change_loader(self, loader):
        self.loader = loader
