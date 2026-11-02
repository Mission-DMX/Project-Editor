"""Unit tests for the gobo-image helpers on :class:`model.ofl.ofl_fixture.WheelSlot`."""

from __future__ import annotations

import base64
import importlib.util
import struct
import sys
import unittest
import zlib
from logging import getLogger

_HAS_PYSIDE = importlib.util.find_spec("PySide6") is not None

logger = getLogger(__name__)
_qapp = None


def setUpModule() -> None:  # noqa: N802 - unittest hook
    global _qapp
    if not _HAS_PYSIDE:
        return
    from PySide6.QtWidgets import QApplication

    _qapp = QApplication.instance() or QApplication(sys.argv)


def _minimal_png_bytes() -> bytes:
    """Hand-encode a 1x1 opaque white PNG so the test needs no fixture files."""

    def _chunk(tag: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + tag
            + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = _chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = _chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


class WheelSlotImageTests(unittest.TestCase):
    """``image_bytes`` is Qt-free; ``pixmap`` is only tested when PySide6 is present."""

    def test_image_bytes_decodes_base64_payload(self) -> None:
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType

        payload = b"a-real-png-payload-doesnt-matter-for-decoding"
        slot = WheelSlot(
            type=WheelSlotType.GOBO,
            name="Test",
            resource={
                "image": {
                    "mimeType": "image/png",
                    "extension": "png",
                    "data": base64.b64encode(payload).decode("ascii"),
                },
            },
        )
        self.assertEqual(payload, slot.image_bytes())
        self.assertEqual("image/png", slot.image_mime_type)

    def test_image_bytes_returns_none_without_resource(self) -> None:
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType

        slot = WheelSlot(type=WheelSlotType.OPEN, name="Open")
        self.assertIsNone(slot.image_bytes())
        self.assertIsNone(slot.image_mime_type)

    def test_image_bytes_returns_none_on_malformed_base64(self) -> None:
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType

        slot = WheelSlot(
            type=WheelSlotType.GOBO,
            name="Broken",
            resource={"image": {"mimeType": "image/png", "data": "@@@not-base64@@@"}},
        )
        self.assertIsNone(slot.image_bytes())

    @unittest.skipUnless(_HAS_PYSIDE, "PySide6 required for pixmap decoding")
    def test_pixmap_roundtrips_a_valid_png(self) -> None:
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType

        slot = WheelSlot(
            type=WheelSlotType.GOBO,
            name="Dot",
            resource={
                "image": {
                    "mimeType": "image/png",
                    "extension": "png",
                    "data": base64.b64encode(_minimal_png_bytes()).decode("ascii"),
                },
            },
        )
        pix = slot.pixmap()
        self.assertIsNotNone(pix)
        self.assertEqual(1, pix.width())
        self.assertEqual(1, pix.height())

    @unittest.skipUnless(_HAS_PYSIDE, "PySide6 required for pixmap decoding")
    def test_pixmap_returns_none_on_undecodable_payload(self) -> None:
        from model.ofl.ofl_fixture import WheelSlot, WheelSlotType

        slot = WheelSlot(
            type=WheelSlotType.GOBO,
            name="Garbled",
            resource={
                "image": {
                    "mimeType": "image/png",
                    "data": base64.b64encode(b"not an image").decode("ascii"),
                },
            },
        )
        self.assertIsNone(slot.pixmap())


if __name__ == "__main__":
    unittest.main()
