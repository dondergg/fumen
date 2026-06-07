"""Regression tests for audit fixes."""

from pathlib import Path

from PIL import Image

from fumen.layout.geometry import compute_layout
from fumen.render.renderer import render_fumen
from fumen.theme import DEFAULT_THEME, TRACK_BLEED, scale_theme
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_barlineoff_hides_measure_divider(tmp_path: Path):
    song, course = parse_tja(FIXTURES / "barline_off.tja", course=0)
    assert not course.measures[0].show_barline
    assert course.measures[1].show_barline
    out = tmp_path / "barline.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    m1, m2 = layout.rows[0][0], layout.rows[0][1]
    header_cy = m2.header_y + (m2.y - m2.header_y) // 2
    assert img.getpixel((m2.x, header_cy)) == DEFAULT_THEME.row_header
    assert img.getpixel((m1.x, header_cy)) == DEFAULT_THEME.measure_divider


def test_cross_row_roll_skips_barline(tmp_path: Path):
    song, course = parse_tja(FIXTURES / "cross_row_roll.tja", course=0)
    m4, m5 = course.measures[3], course.measures[4]
    assert m4.span_notes[0].continues_to_next
    assert m5.span_notes[0].continues_from_prev
    out = tmp_path / "cross_row.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    m3_rect, m5_rect = layout.rows[0][2], layout.rows[1][0]
    header_cy_row1 = m5_rect.header_y + (m5_rect.y - m5_rect.header_y) // 2
    header_cy_row0 = layout.rows[0][0].header_y + (
        layout.rows[0][0].y - layout.rows[0][0].header_y
    ) // 2
    assert img.getpixel((m5_rect.x, header_cy_row1)) == DEFAULT_THEME.row_header
    assert img.getpixel((m3_rect.x + m3_rect.width, header_cy_row0)) == DEFAULT_THEME.measure_divider


def test_chart_starts_below_page_padding(tmp_path: Path):
    _, course = parse_tja(FIXTURES / "simple.tja")
    layout = compute_layout(course, DEFAULT_THEME)
    assert layout.rows[0][0].header_y == DEFAULT_THEME.page_padding_top


def test_scale_theme_preserves_bleed_and_lane_stack():
    scaled = scale_theme(DEFAULT_THEME, 1280)
    assert scaled.page_width == 1280
    assert scaled.track_bleed_x >= TRACK_BLEED
    assert scaled.lane_height > 2 * scaled.lane_border_width + 2 * scaled.lane_border_accent_width
