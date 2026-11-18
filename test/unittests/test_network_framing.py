"""Unit tests for the fish/editor message-framing reader.

These tests pin down the specific desync modes the previous
``_on_ready_read`` implementation hit:

  * Multi-byte type varint (``msg_type >= 128``) misread as a single byte.
  * Zero-length message body offset mis-calculated by ``log2(0+1)/7``.
  * ``readyRead`` delivering the framing header split across chunks.
  * ``readyRead`` delivering the body split across chunks.
  * ``readyRead`` delivering several complete messages concatenated.

The stream parser now buffers partial reads and decodes varints
end-to-end, so all of these cases produce the right ``(msg_type, body)``
without interpreting payload bytes as the next header. That was the
root cause of the sporadic ``Received not implemented message type: X``
warnings observed in live shows.
"""

from __future__ import annotations

import unittest

import varint

from controller.network import NetworkManager, _read_varint, _VarintIncomplete


def _frame(msg_type: int, body: bytes) -> bytes:
    """Build one wire-format message exactly like fish's writer does."""
    return varint.encode(msg_type) + varint.encode(len(body)) + body


class ReadVarintTest(unittest.TestCase):

    def test_single_byte_varint(self) -> None:
        self.assertEqual((14, 1), _read_varint(b"\x0e", 0))

    def test_two_byte_varint(self) -> None:
        """Type values >= 128 need two bytes; the previous reader looked at
        only the first byte and silently decoded to 0 or an EOFError."""
        self.assertEqual((200, 2), _read_varint(varint.encode(200), 0))
        self.assertEqual((300, 2), _read_varint(varint.encode(300), 0))

    def test_zero_value_still_takes_one_byte(self) -> None:
        self.assertEqual((0, 1), _read_varint(b"\x00", 0))

    def test_incomplete_raises_sentinel(self) -> None:
        """A split varint must NOT raise ``EOFError`` or decode garbage; it
        must signal "need more bytes" so the reader can wait for the next
        chunk without disconnecting the socket."""
        with self.assertRaises(_VarintIncomplete):
            _read_varint(b"\xc8", 0)  # high bit set; waiting for continuation
        with self.assertRaises(_VarintIncomplete):
            _read_varint(b"", 0)

    def test_offset_respected(self) -> None:
        buf = b"\xff\x0e\x05"
        self.assertEqual((14, 1), _read_varint(buf, 1))
        self.assertEqual((5, 1), _read_varint(buf, 2))

    def test_overflow_rejected(self) -> None:
        """A varint longer than 10 bytes indicates real stream corruption;
        the previous parser would have spin-looped or run off the buffer."""
        with self.assertRaises(ValueError):
            _read_varint(b"\xff" * 11, 0)


class TryParseOneMessageTest(unittest.TestCase):

    def test_single_complete_message(self) -> None:
        frame = _frame(14, b"HELLO")
        got = NetworkManager._try_parse_one_message(frame)
        self.assertEqual((14, b"HELLO", len(frame)), got)

    def test_zero_length_body(self) -> None:
        """Previously the ``log2(msg_len+1)/7`` offset computation collapsed
        to 0 for zero-length payloads, swallowing the next message's first
        byte and desyncing every message that followed."""
        frame = _frame(7, b"")
        got = NetworkManager._try_parse_one_message(frame)
        self.assertEqual((7, b"", len(frame)), got)

    def test_multi_byte_type_varint(self) -> None:
        frame = _frame(300, b"\x01\x02\x03")
        got = NetworkManager._try_parse_one_message(frame)
        self.assertEqual((300, b"\x01\x02\x03", len(frame)), got)

    def test_split_header_returns_none(self) -> None:
        """Only the type byte has arrived; must wait for the length varint."""
        self.assertIsNone(NetworkManager._try_parse_one_message(varint.encode(14)))

    def test_split_body_returns_none(self) -> None:
        """Header complete, body not yet fully arrived."""
        frame = _frame(14, b"ABCDE")
        half = frame[: len(frame) - 2]
        self.assertIsNone(NetworkManager._try_parse_one_message(half))

    def test_multi_message_only_first_consumed(self) -> None:
        """When two messages are concatenated in one socket chunk, parse
        returns only the first. The caller re-enters the loop with the
        tail bytes and extracts the second message on the next pass."""
        a = _frame(14, b"ABC")
        b = _frame(7, b"XY")
        got = NetworkManager._try_parse_one_message(a + b)
        self.assertEqual((14, b"ABC", len(a)), got)
        # Second pass over the remainder yields the second message.
        tail = (a + b)[len(a):]
        got2 = NetworkManager._try_parse_one_message(tail)
        self.assertEqual((7, b"XY", len(b)), got2)

    def test_empty_buffer_returns_none(self) -> None:
        self.assertIsNone(NetworkManager._try_parse_one_message(b""))


if __name__ == "__main__":
    unittest.main()
