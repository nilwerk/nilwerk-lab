#!/usr/bin/env python3
"""Check that assets/adaptive-icon-foreground-1024.png is RGBA (PNG colour type 6) and its corner pixel is fully transparent.
Usage: python3 -I check_adaptive_icon.py -> exit 1 on failure. (Pure standard library: zlib + struct.)"""
import pathlib
import struct
import sys
import zlib

p = pathlib.Path(__file__).resolve().parent / "assets" / "adaptive-icon-foreground-1024.png"
d = p.read_bytes()
ctype, depth = d[25], d[24]
pos, idat = 8, b""
while pos < len(d):
    (n,) = struct.unpack(">I", d[pos : pos + 4])
    if d[pos + 4 : pos + 8] == b"IDAT":
        idat += d[pos + 8 : pos + 8 + n]
    pos += 12 + n
raw = zlib.decompress(idat)
first = tuple(raw[1:5])  # first scanline, first pixel (every PNG filter returns the raw value there)
ok = ctype == 6 and depth == 8 and first[3] == 0
print(f"colour type {ctype}, bit depth {depth}, first pixel RGBA {first}: {'OK' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
