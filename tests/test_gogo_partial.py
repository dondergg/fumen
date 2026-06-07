"""Partial gogo salmon band in measure headers."""

from pathlib import Path

from PIL import Image

from fumen.layout.geometry import compute_layout
from fumen.render.renderer import render_fumen
from fumen.theme import DEFAULT_THEME
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def _slot_mid_x(rect, slot: int, num_slots: int) -> int:
    x0 = rect.slot_x(slot, num_slots)
    x1 = rect.slot_x(slot + 1, num_slots)
    return int((x0 + x1) / 2)


def test_partial_gogo_parser_slots():
    _, course = parse_tja(FIXTURES / "partial_gogo.tja", course=0)
    m1 = course.measures[0]
    assert m1.gogo
    assert m1.gogo_start_slot == 2
    assert m1.gogo_end_slot == 3


def test_partial_gogo_header_colors(tmp_path: Path):
    song, course = parse_tja(FIXTURES / "partial_gogo.tja", course=0)
    out = tmp_path / "partial_gogo.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    rect = layout.rows[0][0]
    m1 = course.measures[0]
    header_cy = rect.header_y + (rect.y - rect.header_y) // 2
    n = len(m1.slots)
    grey_x = _slot_mid_x(rect, 0, n)
    pink_x = _slot_mid_x(rect, 2, n)
    assert img.getpixel((grey_x, header_cy)) == DEFAULT_THEME.row_header
    assert img.getpixel((pink_x, header_cy)) == DEFAULT_THEME.row_header_gogo


def test_partial_gogo_lane_colors(tmp_path: Path):
    song, course = parse_tja(FIXTURES / "partial_gogo.tja", course=0)
    out = tmp_path / "partial_gogo.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    rect = layout.rows[0][0]
    m1 = course.measures[0]
    inset = DEFAULT_THEME.lane_border_width + DEFAULT_THEME.lane_border_accent_width
    lane_cy = rect.y + inset + 2
    n = len(m1.slots)
    grey_x = _slot_mid_x(rect, 0, n)
    pink_x = _slot_mid_x(rect, 2, n)
    assert img.getpixel((grey_x, lane_cy)) == DEFAULT_THEME.lane_bg
    assert img.getpixel((pink_x, lane_cy)) == DEFAULT_THEME.lane_gogo
