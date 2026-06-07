import json
from pathlib import Path

from PIL import Image

from fumen.layout.geometry import compute_layout
from fumen.render.renderer import render_fumen
from fumen.theme import DEFAULT_THEME
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


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


def test_showcase_golden_probes(tmp_path: Path):
    expected = json.loads((FIXTURES / "golden_probes.json").read_text())
    song, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    out = tmp_path / "showcase.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    coords = _probe_coords(course, layout)

    for name, rgb in expected.items():
        x, y = coords[name]
        assert list(img.getpixel((x, y))) == rgb, name
