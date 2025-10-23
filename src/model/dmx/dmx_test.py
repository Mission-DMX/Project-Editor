from PySide6 import QtCore
from model.broadcaster import Broadcaster
import proto.DirectMode_pb2 as pb

class dmx_test(QtCore.QObject):
    PAN_MAX_DEG  = 540.0
    TILT_MAX_DEG = 270.0

    def __init__(self, universe_id: int, start_address_1based: int, parent=None):
        super().__init__(parent)
        self.universe_id = int(universe_id)
        self.start_idx = start_address_1based - 1

        self._bc = Broadcaster()
        self._bc.dmx_from_fish.connect(self._on_dmx)

        print(f"[movinghead] universe={self.universe_id}, start_address={start_address_1based}")

    @QtCore.Slot(pb.dmx_output)
    def _on_dmx(self, msg: pb.dmx_output) -> None:

        print("a")

        if msg.universe_id != self.universe_id:
            return

        data = list(msg.channel_data)
        if len(data) == 513:
            data = data[1:]
        if len(data) != 512:
            data = (data + [0] * 512)[:512]

        s = self.start_idx

        def u16(coarse: int, fine: int) -> int:
            return (((int(coarse) << 8) | int(fine)) & 0xFFFF)

        pan  = u16(data[s + 0], data[s + 1])
        tilt = u16(data[s + 2], data[s + 3])
        dim    = int(data[s + 5])

        pan_deg   = self.PAN_MAX_DEG  * (pan  / 65535.0)
        tilt_deg  = self.TILT_MAX_DEG * (tilt / 65535.0)
        intensity = max(0, min(255, dim)) / 255.0

        print(f"[movinghead] pan={pan_deg}°  tilt={tilt_deg}°  intensity={intensity}")

