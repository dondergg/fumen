#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from fumen.layout.geometry import compute_layout
from fumen.render.renderer import render_fumen
from fumen.theme import DEFAULT_THEME
from fumen.tja.parser import parse_tja

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
OUT = FIXTURES / "golden_probes.json"


def _probe_coords(course, layout):
    m1 = layout.rows[0][0]
    m7 = layout.rows[1][2]
    header_h = m1.y - m1.header_y
    header_cy = m1.header_y + header_h // 2
    lane_cy = m1.y + m1.height // 2
    m7_cy = m7.header_y + header_h // 2
    don_x = int(m1.slot_x(0, len(course.measures[0].slots)))
    return {
        "page_margin": (10, 10),
        "m1_header_grey": (m1.x + 30, header_cy),
        "m7_header_grey": (m7.x + 30, m7_cy),
        "m1_lane_grey": (m1.x + 40, lane_cy),
        "m1_lane_black_border": (m1.x + 40, m1.y),
        "m1_don_pixel": (don_x, lane_cy),
    }


def main() -> None:
    song, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    tmp = FIXTURES / "_probe.png"
    render_fumen(song, course, tmp, width=816)
    img = Image.open(tmp).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    coords = _probe_coords(course, layout)
    probes = {
        name: list(img.getpixel((x, y))) for name, (x, y) in coords.items()
    }
    OUT.write_text(json.dumps(probes, indent=2) + "\n")
    tmp.unlink(missing_ok=True)
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(probes)} probes)")


if __name__ == "__main__":
    main()
