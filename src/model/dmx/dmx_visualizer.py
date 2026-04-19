"""Polls live DMX data from Fish and writes it into stage fixtures.

Receives DMX frames via the Broadcaster, maps the raw 8-bit channel
values onto MovingHead properties (pan, tilt, dimmer, beam color) and
emits ``fixtures_updated`` so the 3D widget can repaint.

Channel offsets are auto-detected from the Open Fixture Library naming
convention of the connected fixture profile.
"""

import logging
from typing import Dict, List

from PySide6 import QtCore

from model.broadcaster import Broadcaster
from model.stage import StageConfig, MovingHead

logger = logging.getLogger(__file__)

# OFL role names we try to detect on each channel.
MOVEMENT_ROLES = [
    "pan_coarse", "pan_fine",
    "tilt_coarse", "tilt_fine",
    "dimmer", "pan_tilt_speed",
]
COLOR_ROLES = ["red", "green", "blue", "white"]
ALL_ROLES = MOVEMENT_ROLES + COLOR_ROLES

# Physical rotation range of typical moving heads.
DEFAULT_PAN_MAX_DEG = 540.0
DEFAULT_TILT_MAX_DEG = 270.0


def _primary(raw_name: str) -> str:
    # OFL joins multi-function channels with "___" - keep only the first part.
    return raw_name.split("___")[0].strip().lower().replace(" ", "_")


def auto_detect_mapping(channel_names: List[str],
                        roles: List[str]) -> Dict[str, int]:
    """Return a {role: channel_offset} dict, -1 where no match was found."""
    mapping = {r: -1 for r in roles}

    for i, raw_name in enumerate(channel_names):
        p = _primary(raw_name)

        # Pan
        if p == "pan_fine" or ("pan" in p and "fine" in p):
            if "pan_fine" in roles:
                mapping["pan_fine"] = i
        elif "pan" in p and "speed" not in p and "tilt" not in p:
            if "pan_coarse" in roles:
                mapping["pan_coarse"] = i

        # Tilt
        if p == "tilt_fine" or ("tilt" in p and "fine" in p):
            if "tilt_fine" in roles:
                mapping["tilt_fine"] = i
        elif "tilt" in p and "speed" not in p and "pan" not in p:
            if "tilt_coarse" in roles:
                mapping["tilt_coarse"] = i

        # Dimmer / speed
        if p in ("dimmer", "intensity") and "dimmer" in roles:
            mapping["dimmer"] = i
        if "speed" in p and ("pan" in p or "tilt" in p):
            if "pan_tilt_speed" in roles:
                mapping["pan_tilt_speed"] = i

        # Colors
        if "red" in p and "red" in roles:
            mapping["red"] = i
        if "green" in p and "green" in roles:
            mapping["green"] = i
        if "blue" in p and "blue" in roles:
            mapping["blue"] = i
        if p == "white" and "white" in roles:
            mapping["white"] = i

    return mapping


class DmxVisualizer(QtCore.QObject):
    """Drives the stage fixtures from incoming DMX frames."""

    fixtures_updated = QtCore.Signal()

    def __init__(self, stage_config: StageConfig,
                 board_configuration=None, parent=None):
        super().__init__(parent)
        self._stage_config = stage_config
        self._board_config = board_configuration
        self._broadcaster = Broadcaster()
        self._enabled = True

        try:
            self._broadcaster.dmx_from_fish.connect(self._on_dmx)
        except Exception as e:
            logger.warning("Could not connect broadcaster signals: %s", e)

        # Request fresh DMX data at ~60 Hz.
        self._poll_timer = QtCore.QTimer(self)
        self._poll_timer.setInterval(16)
        self._poll_timer.timeout.connect(self._request_dmx)
        self._poll_timer.start()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        if value:
            self._poll_timer.start()
        else:
            self._poll_timer.stop()

    def _request_dmx(self):
        if not self._enabled or self._board_config is None:
            return
        try:
            for universe in self._board_config.universes:
                self._broadcaster.send_request_dmx_data.emit(universe)
        except Exception:
            pass

    @QtCore.Slot()
    def _on_dmx(self, msg) -> None:
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

    def _apply_movement(self, obj, raw, cfg):
        """Map pan/tilt/dimmer channels to the fixture's 2-DOF properties."""
        start = cfg.get("start_channel", 0)
        m = cfg.get("mapping", {})

        def rd(role):
            off = m.get(role, -1)
            if off < 0 or not (0 <= start + off < 512):
                return None
            return int(raw[start + off])

        # 16-bit pan, centered at zero.
        pc, pf = rd("pan_coarse"), rd("pan_fine")
        if pc is not None:
            v = (pc << 8) | (pf or 0)
            obj.pan = (v / 65535.0) * DEFAULT_PAN_MAX_DEG - DEFAULT_PAN_MAX_DEG / 2.0

        # 16-bit tilt, centered at zero.
        tc, tf = rd("tilt_coarse"), rd("tilt_fine")
        if tc is not None:
            v = (tc << 8) | (tf or 0)
            obj.tilt = (v / 65535.0) * DEFAULT_TILT_MAX_DEG - DEFAULT_TILT_MAX_DEG / 2.0

        dim = rd("dimmer")
        if dim is not None:
            obj.dimmer = dim / 255.0
            obj.beam_on = dim > 0

    def _apply_color(self, obj, raw, cfg):
        """Map R/G/B/W channels to beam_color."""
        start = cfg.get("start_channel", 0)
        m = cfg.get("mapping", {})

        def rd(role):
            off = m.get(role, -1)
            if off < 0 or not (0 <= start + off < 512):
                return None
            return int(raw[start + off])

        r, g, b = rd("red"), rd("green"), rd("blue")
        if r is None or g is None or b is None:
            return

        # White LED adds on top of RGB (matches RGBW fixtures).
        w = rd("white")
        if w is not None and w > 0:
            r = min(255, r + w)
            g = min(255, g + w)
            b = min(255, b + w)

        obj.beam_color = (r, g, b)
        any_color = (r > 0 or g > 0 or b > 0)
        obj.beam_on = any_color

        # Use the white channel as dimmer if no dedicated movement dimmer exists.
        if w is not None:
            obj.dimmer = w / 255.0 if w > 0 else (1.0 if any_color else 0.0)
        elif not self._has_movement_dimmer(obj) and any_color:
            obj.dimmer = 1.0

    def _has_movement_dimmer(self, obj) -> bool:
        dc = obj.device_config
        if not dc:
            return False
        return dc.get("movement", {}).get("mapping", {}).get("dimmer", -1) >= 0
