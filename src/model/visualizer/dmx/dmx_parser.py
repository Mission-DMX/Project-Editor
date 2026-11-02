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
from model.color_hsi import ColorHSI
from model.visualizer.stage.so_moving_head import MovingHead
from model.visualizer.stage.so_par_can import ParCan
from model.visualizer.stage.so_pixel_fixture import PixelFixture

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    import proto.DirectMode_pb2
    from model import BoardConfiguration
    from model.ofl.fixture import UsedFixture
    from model.visualizer.stage.stage_config import StageConfig

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
    AMBER = "amber"
    UV = "uv"


# Base RGB colours used when mixing per-role channel values into a single beam
# colour. Values match ``model.visualizer.dmx.dmx_parser._PIXEL_BASE_COLOURS`` so
# per-pixel and per-fixture colour mixing stay visually consistent.
_COLOR_ROLE_BASES: dict[ColorRole, tuple[int, int, int]] = {
    ColorRole.RED: (255, 0, 0),
    ColorRole.GREEN: (0, 255, 0),
    ColorRole.BLUE: (0, 0, 255),
    ColorRole.WHITE: (255, 255, 255),
    ColorRole.AMBER: (255, 191, 0),
    ColorRole.UV: (140, 0, 255),
}


# Physical rotation range of typical moving heads.
DEFAULT_PAN_MAX_DEG = 540.0
DEFAULT_TILT_MAX_DEG = 270.0

# Base colours for each per-pixel channel role at 100% DMX. Ordered so that mixing
# behaves consistently between fixture types; the exact values for white variants
# come from :class:`ColorHSI` and typical stage-lighting colour-temperature ratings.
_WARM_WHITE_KELVIN = 3200.0
_COLD_WHITE_KELVIN = 6500.0
_PIXEL_BASE_COLOURS: tuple[tuple[str, tuple[int, int, int]], ...] = (
    ("r", (255, 0, 0)),
    ("g", (0, 255, 0)),
    ("b", (0, 0, 255)),
    ("w", (255, 255, 255)),
    ("ww", ColorHSI.from_color_temperature(_WARM_WHITE_KELVIN).to_rgb()),
    ("cw", ColorHSI.from_color_temperature(_COLD_WHITE_KELVIN).to_rgb()),
    ("a", (255, 191, 0)),
    ("uv", (140, 0, 255)),
)


def default_pan_tilt_range() -> tuple[float, float, float, float]:
    """Default pan/tilt axis limits in degrees, used when no fixture definition is available."""
    return (
        -DEFAULT_PAN_MAX_DEG / 2.0,
        DEFAULT_PAN_MAX_DEG / 2.0,
        -DEFAULT_TILT_MAX_DEG / 2.0,
        DEFAULT_TILT_MAX_DEG / 2.0,
    )


def _primary(raw_name: str) -> str:
    # OFL joins multi-function channels with "___" - keep only the first part.
    return raw_name.split("___", maxsplit=1)[0].strip().lower().replace(" ", "_")


def auto_detect_mapping(channel_names: list[str], roles: type[MovementRole | ColorRole]) -> dict[str, int]:
    """Return a {role: channel_offset} dict, -1 where no match was found.

    ``roles`` is one of the role enum classes; only channels matching that class are detected.
    The returned mapping (like every mapping dict stored in a ``device_config``) uses plain
    ``str`` keys (``role.value``) so it survives ruamel.yaml serialization. Read persisted
    mappings with ``role.value`` to keep that boundary explicit.
    """
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
        if "amber" in p and ColorRole.AMBER in roles:
            mapping[ColorRole.AMBER] = i
        # UV / ultraviolet — match on the primary token to avoid catching "cover".
        if (p == "uv" or p == "ultraviolet") and ColorRole.UV in roles:
            mapping[ColorRole.UV] = i

    # ruamel.yaml cannot represent StrEnum members, so normalize keys to plain strings.
    return {str(role): offset for role, offset in mapping.items()}


def parse_pan_tilt_range(value: object) -> tuple[float, float, float, float]:
    """Normalize a persisted ``pan_tilt_range`` entry into axis limits.

    Accepts the current 4-tuple ``(pan_min, pan_max, tilt_min, tilt_max)`` form as well
    as the legacy 2-tuple ``(pan_span, tilt_span)`` form written by older editor
    versions, which assumed axis ranges centered on zero.

    Returns:
        The axis limits in degrees; the default limits for anything else.

    """
    if isinstance(value, (list, tuple)):
        try:
            if len(value) == 4:
                pan_min, pan_max, tilt_min, tilt_max = (float(v) for v in value)
                if pan_max < pan_min:
                    pan_min, pan_max = pan_max, pan_min
                if tilt_max < tilt_min:
                    tilt_min, tilt_max = tilt_max, tilt_min
                return pan_min, pan_max, tilt_min, tilt_max
            if len(value) == 2:
                pan_span, tilt_span = (abs(float(v)) for v in value)
                return (-pan_span / 2.0, pan_span / 2.0, -tilt_span / 2.0, tilt_span / 2.0)
        except (TypeError, ValueError):
            logger.warning("Cannot interpret pan_tilt_range %r; using defaults.", value)
    return default_pan_tilt_range()


def get_movement_range(fixture: UsedFixture) -> tuple[float, float, float, float]:
    """Get the movement limits of the fixture's pan/tilt axes in degrees.

    Returns:
        ``(pan_min, pan_max, tilt_min, tilt_max)``; the default limits if the fixture
        definition provides no usable angle information.

    """
    limits = fixture.axis_movement_limits
    if limits is None:
        return default_pan_tilt_range()
    (pan_min, pan_max), (tilt_min, tilt_max) = limits
    return pan_min, pan_max, tilt_min, tilt_max


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

    def set_stage_config(self, stage_config: StageConfig) -> None:
        """Swap the stage configuration whose objects are driven by DMX frames."""
        self._stage_config = stage_config

    def _request_dmx(self) -> None:
        if not self._enabled or self._board_config is None:
            return
        try:
            for universe in self._board_config.universes:
                self._broadcaster.send_request_dmx_data.emit(universe)
        except Exception as e:
            logger.exception("Could not send DMX request: %s", e)

    @QtCore.Slot(object)
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
            dc = obj.device_config
            if not dc:
                continue

            if isinstance(obj, (MovingHead, ParCan)):
                # ParCans reuse the movement section purely for their dimmer channel
                # (no pan/tilt mapping); ``_apply_movement`` only touches fields that
                # have a channel mapped so leaving pan/tilt at -1 is a no-op.
                mv = dc.get("movement")
                if mv and mv.get("universe", -1) == universe_id:
                    self._apply_movement(obj, raw, mv)
                    any_updated = True

                col = dc.get("color")
                if col and col.get("universe", -1) == universe_id:
                    self._apply_color(obj, raw, col)
                    any_updated = True
            elif isinstance(obj, PixelFixture):
                pixels = dc.get("pixels")
                if pixels and pixels.get("universe", -1) == universe_id:
                    self._apply_pixels(obj, raw, pixels)
                    any_updated = True

        if any_updated:
            self.fixtures_updated.emit()

    def _apply_movement(self, obj: MovingHead, raw: list[int], cfg: dict[str, Any]) -> None:
        """Map pan/tilt/dimmer channels to the fixture's 2-DOF properties."""
        start = cfg.get("start_channel", 0)
        channel_mapping = cfg.get("mapping", {})

        def rd(role: MovementRole) -> int | None:
            off = channel_mapping.get(role.value, -1)
            if off < 0 or not (0 <= start + off < 512):
                return None
            return int(raw[start + off])

        pan_min, pan_max, tilt_min, tilt_max = parse_pan_tilt_range(cfg.get("pan_tilt_range"))

        # 16-bit pan: DMX 0..65535 maps linearly onto [pan_min, pan_max].
        pc, pf = rd(MovementRole.PAN_COARSE), rd(MovementRole.PAN_FINE)
        if pc is not None:
            v = (pc << 8) | (pf or 0)
            obj.pan = pan_min + (pan_max - pan_min) * (v / 65535.0)

        # 16-bit tilt: DMX 0..65535 maps linearly onto [tilt_min, tilt_max].
        tc, tf = rd(MovementRole.TILT_COARSE), rd(MovementRole.TILT_FINE)
        if tc is not None:
            v = (tc << 8) | (tf or 0)
            obj.tilt = tilt_min + (tilt_max - tilt_min) * (v / 65535.0)

        dim = rd(MovementRole.DIMMER)
        if dim is not None:
            obj.dimmer = dim / 255.0
            obj.update_beam_state()

    def _apply_color(self, obj: MovingHead, raw: list[int], cfg: dict[str, Any]) -> None:
        """Mix every mapped colour channel into ``obj.beam_color``.

        Each role's DMX value scales its base RGB colour from
        :data:`_COLOR_ROLE_BASES` (red=(255,0,0), amber=(255,191,0), UV=(140,0,255)…)
        and the results are summed and clamped, so a fixture like the Stairville
        CX60 Hex — which carries dedicated amber and UV LEDs on top of RGBW —
        produces the correct blended colour when those channels are driven.
        """
        start = cfg.get("start_channel", 0)
        m = cfg.get("mapping", {})

        def rd(role: ColorRole) -> int | None:
            off = m.get(role.value, -1)
            if off < 0 or not (0 <= start + off < 512):
                return None
            return int(raw[start + off])

        r_total = g_total = b_total = 0.0
        any_mapped = False
        for role, base in _COLOR_ROLE_BASES.items():
            v = rd(role)
            if v is None:
                continue
            any_mapped = True
            if v <= 0:
                continue
            frac = v / 255.0
            r_total += base[0] * frac
            g_total += base[1] * frac
            b_total += base[2] * frac

        # Add the current colour-wheel slot's colour on top of any direct RGB. For
        # wheel-only fixtures (no R/G/B channels at all) the wheel is the sole
        # colour source — otherwise it tints whatever RGB mix the user dialed in.
        wheel_cfg = cfg.get("wheel")
        wheel_color = self._lookup_wheel_color(raw, wheel_cfg)
        if wheel_cfg is not None:
            any_mapped = True
        if wheel_color is not None:
            r_total += wheel_color[0]
            g_total += wheel_color[1]
            b_total += wheel_color[2]

        if not any_mapped:
            # No colour channel mapped (or all out of range); nothing to apply.
            return

        r = int(min(255.0, r_total))
        g = int(min(255.0, g_total))
        b = int(min(255.0, b_total))

        obj.beam_color = (r, g, b)
        obj.update_beam_state()

        # Keep the emissive-lens colour in sync too. For fixtures whose
        # ``lense_colors`` is a @property (e.g. :class:`ParCan`) this mutation is
        # a no-op — the property reads ``beam_color`` above — but for
        # :class:`MovingHead`, which stores the list, we still need to update
        # each entry so the lens renders the new colour.
        for lense_light in obj.lense_colors:
            lense_light.color = (r, g, b)

    def _apply_pixels(self, obj: PixelFixture, raw: list[int], cfg: dict[str, Any]) -> None:
        """Update every pixel colour of a :class:`PixelFixture` from the DMX frame.

        Per-pixel entries in ``cfg["channels"]`` list any of the short keys
        below, each holding an absolute universe channel index (missing =
        unmapped). Every mapped channel contributes to the pixel's RGB by
        scaling its base colour by ``raw[ch] / 255``:

        * ``r``, ``g``, ``b`` — primary colour channels
        * ``w`` — plain white LED
        * ``cw`` / ``ww`` — cold / warm white (temperature-blended)
        * ``a`` — amber, ``uv`` — ultraviolet

        A fixture-wide ``cfg["wheel"]`` (colour wheel) is looked up by DMX value
        and its slot colour is added into every pixel. ``cfg["dimmer"]`` scales
        the final pixel RGB. Fixtures that carry only a dimmer channel (no colour
        source at all) fall back to a plain-white base so the dimmer produces a
        visible white output.
        """
        pixel_count = obj.pixel_matrix[0] * obj.pixel_matrix[1]
        channels = cfg.get("channels") or []
        dimmer_channel = int(cfg.get("dimmer", -1))
        dimmer = raw[dimmer_channel] / 255.0 if 0 <= dimmer_channel < 512 else 1.0
        wheel_color = self._lookup_wheel_color(raw, cfg.get("wheel"))

        for i in range(pixel_count):
            entry = channels[i] if i < len(channels) and isinstance(channels[i], dict) else {}
            r, g, b = self._compose_pixel_color(raw, entry, wheel_color)
            r = int(min(255.0, r * dimmer))
            g = int(min(255.0, g * dimmer))
            b = int(min(255.0, b * dimmer))
            obj.set_pixel_color(i, (r, g, b))

    def _compose_pixel_color(
        self,
        raw: list[int],
        entry: dict[str, int],
        wheel_color: tuple[int, int, int] | None,
    ) -> tuple[float, float, float]:
        """Sum the colour contributions declared in a single pixel entry.

        Returns the pre-dimmer ``(r, g, b)`` in floating point 0-255 range. If
        no channel contributes at all — as with pure dimmer-only fixtures — a
        plain-white base is returned so the caller's dimmer multiplication still
        produces visible white light.
        """
        r_total = g_total = b_total = 0.0
        has_contribution = False

        for role_key, base in _PIXEL_BASE_COLOURS:
            ch = int(entry.get(role_key, -1))
            if not (0 <= ch < 512):
                continue
            frac = raw[ch] / 255.0
            if frac <= 0.0:
                # Zero-value channels contribute nothing but still count as "mapped"
                # so the dimmer-only fallback doesn't kick in for a black RGB signal.
                has_contribution = True
                continue
            r_total += base[0] * frac
            g_total += base[1] * frac
            b_total += base[2] * frac
            has_contribution = True

        if wheel_color is not None:
            r_total += wheel_color[0]
            g_total += wheel_color[1]
            b_total += wheel_color[2]
            has_contribution = True

        if not has_contribution:
            # Fixture exposes only a dimmer (or nothing colour-related was mapped);
            # treat the emitted light as plain white so the dimmer becomes visible.
            r_total = g_total = b_total = 255.0

        return r_total, g_total, b_total

    def _lookup_wheel_color(
        self, raw: list[int], wheel_cfg: dict[str, Any] | None
    ) -> tuple[int, int, int] | None:
        """Find the wheel slot covering the current DMX value and return its RGB.

        Falls back to the nearest slot by centre distance if no range contains
        the DMX value exactly — this handles fixtures whose OFL definitions
        leave small gaps between slot capabilities.
        """
        if not wheel_cfg:
            return None
        ch = int(wheel_cfg.get("channel", -1))
        if not (0 <= ch < 512):
            return None
        slots = wheel_cfg.get("slots") or []
        if not slots:
            return None
        dmx_value = int(raw[ch])

        best: dict[str, Any] | None = None
        best_dist: float = float("inf")
        for slot in slots:
            dmx_min = int(slot.get("dmx_min", 0))
            dmx_max = int(slot.get("dmx_max", dmx_min))
            if dmx_min <= dmx_value <= dmx_max:
                best = slot
                break
            center = (dmx_min + dmx_max) / 2.0
            dist = abs(dmx_value - center)
            if dist < best_dist:
                best_dist = dist
                best = slot

        if best is None:
            return None
        c = best.get("color", [0, 0, 0])
        return int(c[0]), int(c[1]), int(c[2])
