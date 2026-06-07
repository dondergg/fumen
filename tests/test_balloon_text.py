"""Balloon hit count is centered in the head."""

from pathlib import Path

from PIL import Image, ImageDraw

from fumen.model import NoteKind
from fumen.render.canvas import _load_font, draw_text_centered
from fumen.render.notes_draw import _balloon_head_radius
from fumen.theme import DEFAULT_THEME


def test_balloon_digit_not_rounded_left_on_half_pixel():
    """cx ending in .5 must not snap 1px left (round-half-to-even)."""
    img = Image.new("RGB", (40, 40), DEFAULT_THEME.balloon)
    draw = ImageDraw.Draw(img)
    font = _load_font(DEFAULT_THEME.font_size_meta, None)
    cx = 633.0
    cy = 223.5
    bbox = draw_text_centered(draw, cx, cy, "2", font, DEFAULT_THEME.balloon_text)
    ink_cx = (bbox[0] + bbox[2]) / 2
    assert abs(ink_cx - cx) < 0.6


def test_big_balloon_head_larger_than_small():
    small = _balloon_head_radius(big=False, theme=DEFAULT_THEME)
    big = _balloon_head_radius(big=True, theme=DEFAULT_THEME)
    assert big > small


def test_big_balloon_tail_matches_big_roll_height():
    from fumen.render.notes_draw import _roll_fill_height

    assert _roll_fill_height(big=True, theme=DEFAULT_THEME) > DEFAULT_THEME.balloon_bar_height


def test_balloon_tail_overlaps_head(tmp_path):
    """Tail starts at head center; joins cleanly with no left-edge slivers."""
    from fumen.layout.geometry import compute_layout
    from fumen.render.notes_draw import (
        _balloon_head_radius,
        _roll_fill_height,
        _span_end_x,
        _span_start_x,
    )
    from fumen.render.renderer import render_fumen
    from fumen.tja.parser import parse_tja

    fixtures = Path(__file__).parent / "fixtures"
    song, course = parse_tja(fixtures / "showcase.tja", course=0)
    out = tmp_path / "balloon.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    m8 = course.measures[7]
    rect = next(r for row in layout.rows for r in row if r.measure.index == 8)
    span = next(s for s in m8.span_notes if s.kind == NoteKind.BALLOON)
    x0 = _span_start_x(rect, span)
    x1 = _span_end_x(rect, span)
    head_r = _balloon_head_radius(big=False, theme=DEFAULT_THEME)
    cx = x0 + head_r
    cy = int(rect.y + rect.height / 2)
    bar_h = _roll_fill_height(big=False, theme=DEFAULT_THEME)
    ow = DEFAULT_THEME.note_outline_outer_width
    iw = DEFAULT_THEME.note_outline_inner_width
    outer_h = bar_h + 2 * (ow + iw)

    assert x1 > cx + head_r
    join_x = int(cx + head_r + 1)
    assert img.getpixel((join_x, cy)) == DEFAULT_THEME.balloon

    # Tail must not begin at x0 — no rectangular bar corners left of center.
    left_probe_y = int(cy - outer_h // 2 - 1)
    left_probe_x = int(x0 + 2)
    assert left_probe_x < cx
    assert img.getpixel((left_probe_x, left_probe_y)) != DEFAULT_THEME.note_outline_outer
