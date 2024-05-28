# coding=utf-8
"""Varint encoder/decoder
varints are a common encoding for variable length integer data, used in
libraries such as sqlite, protobuf, v8, and more.
Here's a quick and dirty module to help avoid reimplementing the same thing
over and over again.
from : https://github.com/fmoo/python-varint/blob/master/varint.py
"""

import sys
# byte-oriented StringIO was moved to io.BytesIO in py3k
from io import BytesIO

if sys.version > '3':
    def _byte(byte):
        return bytes((byte,))
else:
    def _byte(byte):
        return chr(byte)


def encode(number):
    """Pack `number` into varint bytes"""
    buf = b''
    while True:
        towrite = number & 0x7f
        number >>= 7
        if number:
            buf += _byte(towrite | 0x80)
        else:
            buf += _byte(towrite)
            break
    return buf


def decode_stream(stream):
    """Read a varint from `stream`"""
    shift = 0
    result = 0
    while True:
        i = _read_one(stream)
        result |= (i & 0x7f) << shift
        shift += 7
        if not i & 0x80:
            break

    return result


def decode_bytes(buf):
    """Read a varint from `buf` bytes"""
    return decode_stream(BytesIO(buf))


def _read_one(stream):
    """Read a byte from the file (as an integer)
    raises EOFError if the stream ends while reading bytes.
    """
    bytes_ = stream.read(1)
    if bytes_ == b'':
        # TODO save showfile backup and exit
        raise EOFError("Unexpected EOF while reading bytes")
    return ord(bytes_)
