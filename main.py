#!/usr/bin/env python3
"""Entry program for the-picture-that-tastes-of-one-20261122-2047.

The picture (one ripe mango, rendered at build time) ships in this
repository as entry.png. This program only copies that finished image
to the grader's output path, using the standard library alone.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
DESTINATION = "/output/entry.png"


def main():
    os.makedirs(os.path.dirname(DESTINATION), exist_ok=True)
    shutil.copyfile(SOURCE, DESTINATION)
    size = os.path.getsize(DESTINATION)
    # sanity check: the output must be a whole PNG (magic bytes + IEND)
    with open(DESTINATION, "rb") as f:
        head = f.read(8)
        f.seek(-12, os.SEEK_END)
        tail = f.read(12)
    if head != b"\x89PNG\r\n\x1a\n" or tail[4:8] != b"IEND":
        raise ValueError("output is not a complete PNG")
    print(f"wrote {DESTINATION} ({size} bytes, valid PNG)")


if __name__ == "__main__":
    main()
