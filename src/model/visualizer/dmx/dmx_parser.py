"""Polls live DMX data from Fish and writes it into stage fixtures.

Receives DMX frames via the Broadcaster, maps the raw 8-bit channel
values onto MovingHead properties (pan, tilt, dimmer, beam color) and
emits ``fixtures_updated`` so the 3D widget can repaint.

Channel offsets are auto-detected from the Open Fixture Library naming
convention of the connected fixture profile.
"""

from __future__ import annotations

from enum import StrEnum
from logging import getLogger
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore

from model.broadcaster import Broadcaster
from model.visualizer.stage.so_moving_head import MovingHead

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    import proto.DirectMode_pb2
    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture
    from model.visualizer.stage.stage_config import StageConfig
    from model.visualizer.stage.stage_object import StageObject

logger = getLogger(__name__)


class MovementRole(StrEnum):
    """OFL channel roles we try to detect for fixture movement."""

    PAN_COARSE = "pan_coarse"
    PAN_FINE = "pan_fine"
    TILT_COARSE = "tilt_coarse"
    TILT_FINE = "tilt_fine"
    DIMMER = "dimmer"
    PAN_TILT_SPEED = "pan_tilt_speed"


class ColorRole(StrEnum):
    """OFL channel roles we try to detect for fixture color mixing."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    WHITE = "white"


# Physical rotation range of typical moving heads.
DEFAULT_PAN_MAX_DEG = 540.0
DEFAULT_TILT_MAX_DEG = 270.0


def _primary(raw_name: str) -> str:
    # OFL joins multi-function channels with "___" - keep only the first part.
    return raw_name.split("___", maxsplit=1)[0].strip().lower().replace(" ", "_")


def auto_detect_mapping(channel_names: list[str], roles: type[MovementRole | ColorRole]) -> dict[str, int]:
    """Return a {role: channel_offset} dict, -1 where no match was found."""
    mapping = dict.fromkeys(roles, -1)

    for i, raw_name in enumerate(channel_names):
        p = _primary(raw_name)

        # Pan
        if (p == MovementRole.PAN_FINE or ("pan" in p and "fine" in p)) and MovementRole.PAN_FINE in roles:
            mapping[MovementRole.PAN_FINE] = i
        elif ("pan" in p and "speed" not in p and "tilt" not in p) and MovementRole.PAN_COARSE in roles:
            mapping[MovementRole.PAN_COARSE] = i

        # Tilt
        if p == MovementRole.TILT_FINE or ("tilt" in p and "fine" in p):
            if MovementRole.TILT_FINE in roles:
                mapping[MovementRole.TILT_FINE] = i
        elif ("tilt" in p and "speed" not in p and "pan" not in p) and MovementRole.TILT_COARSE in roles:
            mapping[MovementRole.TILT_COARSE] = i

        # Dimmer / speed
        if p in (MovementRole.DIMMER, "intensity") and MovementRole.DIMMER in roles:
            mapping[MovementRole.DIMMER] = i
        if "speed" in p and ("pan" in p or "tilt" in p) and MovementRole.PAN_TILT_SPEED in roles:
            mapping[MovementRole.PAN_TILT_SPEED] = i

        # Colors
        if "red" in p and ColorRole.RED in roles:
            mapping[ColorRole.RED] = i
        if "green" in p and ColorRole.GREEN in roles:
            mapping[ColorRole.GREEN] = i
        if "blue" in p and ColorRole.BLUE in roles:
            mapping[ColorRole.BLUE] = i
        if p == ColorRole.WHITE and ColorRole.WHITE in roles:
            mapping[ColorRole.WHITE] = i

    # ruamel.yaml cannot represent StrEnum members, so normalize keys to plain strings.
    return {str(role): offset for role, offset in mapping.items()}


def get_movement_range(fixture: UsedFixture) -> tuple[float, float]:
    """Get the range in which the fixture can move the pan / tilt axis."""
    return fixture.maximum_axis_movement or (DEFAULT_PAN_MAX_DEG, DEFAULT_TILT_MAX_DEG)


class DmxParser(QtCore.QObject):
    """Drives the stage fixtures from incoming DMX frames."""

    fixtures_updated = QtCore.Signal()

    def __init__(
        self,
        stage_config: StageConfig,
        board_configuration: BoardConfiguration | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize DMX to stage visualizer adapter."""
        super().__init__(parent)
        self._stage_config = stage_config
        self._board_config = board_configuration
        self._broadcaster = Broadcaster()
        self._enabled = True

        try:
            self._broadcaster.dmx_from_fish.connect(self._on_dmx)
        except Exception as e:
            logger.warning("Could not connect broadcaster signals: %s", e)

        # Request fresh DMX data at ~45 Hz.
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.setInterval(22)
        self._poll_timer.timeout.connect(self._request_dmx)
        self._poll_timer.start()

    @property
    def enabled(self) -> bool:
        """Enable or disable the live updating with DMX values from fish."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if value:
            self._poll_timer.start()
        else:
            self._poll_timer.stop()

    def _request_dmx(self) -> None:
        if not self._enabled or self._board_config is None:
            return
        try:
            for universe in self._board_config.universes:
                self._broadcaster.send_request_dmx_data.emit(universe)
        except Exception as e:
            logger.exception("Could not send DMX request: %s", e)

    @QtCore.Slot()
    def _on_dmx(self, msg: proto.DirectMode_pb2.dmx_output) -> None:
        if not self._enabled:
            return

        universe_id = msg.universe_id

        # Normalize to exactly 512 channels; Fish sometimes sends a leading zero.
        raw = list(msg.channel_data)
        if len(raw) == 513:
            raw = raw[1:]
        raw = (raw + [0] * 512)[:512]

        any_updated = False
        for obj in self._stage_config.objects:
            if not isinstance(obj, MovingHead):
                continue
            dc = obj.device_config
            if not dc:
                continue

            mv = dc.get("movement")
            if mv and mv.get("universe", -1) == universe_id:
                self._apply_movement(obj, raw, mv)
                any_updated = True

            col = dc.get("color")
            if col and col.get("universe", -1) == universe_id:
                self._apply_color(obj, raw, col)
                any_updated = True

        if any_updated:
            self.fixtures_updated.emit()

    def _apply_movement(self, obj: StageObject, raw: list[int], cfg: dict[str, Any]) -> None:
        """Map pan/tilt/dimmer channels to the fixture's 2-DOF properties."""
        start = cfg.get("start_channel", 0)
        channel_mapping = cfg.get("mapping", {})

        def rd(role: MovementRole) -> int | None:
            off = channel_mapping.get(role, -1)
            if off < 0 or not (0 <= start + off < 512):
                return None
            return int(raw[start + off])

        pan_max_deg, tilt_max_deg = cfg.get("pan_tilt_range", (DEFAULT_PAN_MAX_DEG, DEFAULT_TILT_MAX_DEG))

        # 16-bit pan, centered at zero.
        pc, pf = rd(MovementRole.PAN_COARSE), rd(MovementRole.PAN_FINE)
        if pc is not None:
            v = (pc << 8) | (pf or 0)
            obj.pan = (v / 65535.0) * pan_max_deg - pan_max_deg / 2.0

        # 16-bit tilt, centered at zero.
        tc, tf = rd(MovementRole.TILT_COARSE), rd(MovementRole.TILT_FINE)
        if tc is not None:
            v = (tc << 8) | (tf or 0)
            obj.tilt = (v / 65535.0) * tilt_max_deg - tilt_max_deg / 2.0

        dim = rd(MovementRole.DIMMER)
        if dim is not None:
            obj.dimmer = dim / 255.0
            obj.beam_on = dim > 0

    def _apply_color(self, obj: StageObject, raw: list[int], cfg: dict[str, Any]) -> None:
        """Map R/G/B/W channels to beam_color."""
        start = cfg.get("start_channel", 0)
        m = cfg.get("mapping", {})

        def rd(role: ColorRole) -> int | None:
            off = m.get(role, -1)
            if off < 0 or not (0 <= start + off < 512):
                return None
            return int(raw[start + off])

        r, g, b = rd(ColorRole.RED), rd(ColorRole.GREEN), rd(ColorRole.BLUE)
        if r is None or g is None or b is None:
            return

        # White LED adds on top of RGB (matches RGBW fixtures).
        w = rd(ColorRole.WHITE)
        if w is not None and w > 0:
            r = min(255, r + w)
            g = min(255, g + w)
            b = min(255, b + w)

        obj.beam_color = (r, g, b)
        any_color = r > 0 or g > 0 or b > 0
        obj.beam_on = any_color

        # Use the white channel as dimmer if no dedicated movement dimmer exists.
        # if w is not None:
        #    obj.dimmer = w / 255.0 if w > 0 else (1.0 if any_color else 0.0)
        if not self._has_movement_dimmer(obj) and any_color:
            obj.dimmer = 1.0
        # TODO if multiple segments are present: apply them in order
        if hasattr(obj, "lense_colors"):
            for lense_light in obj.lense_colors:
                lense_light.color = (r, g, b)

    def _has_movement_dimmer(self, obj: StageObject) -> bool:
        dc = obj.device_config
        if not dc:
            return False
        return dc.get("movement", {}).get("mapping", {}).get(MovementRole.DIMMER, -1) >= 0
