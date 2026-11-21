#!/usr/bin/env python3
"""MERROW — The Poster for a Place That Isn't There (make.fun entry).

Writes the travel poster to /output/entry.png. Standard library only:
the poster PNG ships beside this file as poster.png and is copied to
the output path. No network, no Pillow, no fonts needed at runtime.
"""

import os
from pathlib import Path

POSTER = Path(__file__).resolve().with_name("poster.png")


def main() -> None:
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = POSTER.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "poster.png is not a PNG"
    tmp = os.path.join(out_dir, ".entry.png.tmp")
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
