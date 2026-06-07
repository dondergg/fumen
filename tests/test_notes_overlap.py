"""Notes sit on slot left edges; overlap from sprite size vs grid pitch."""

from pathlib import Path

from PIL import Image

from fumen.layout.geometry import compute_layout
from fumen.model import NoteKind
from fumen.render.notes_draw import _note_radius
from fumen.render.renderer import render_fumen
from fumen.theme import DEFAULT_THEME
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def _measure_rect(layout, measure_index: int):
    for row in layout.rows:
        for rect in row:
            if rect.measure.index == measure_index:
                return rect
    raise KeyError(measure_index)


def _hit_centers(rect, measure) -> list[float]:
    n = len(measure.slots) or 1
    return [
        rect.slot_x(note.slot, n)
        for note in sorted(measure.hit_notes, key=lambda n: n.slot)
    ]


def test_all_normal_notes_same_radius():
    _, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    m1 = course.measures[0]
    layout = compute_layout(course, DEFAULT_THEME)
    rect = layout.rows[0][0]
    base_r = DEFAULT_THEME.note_diameter // 2
    for note in m1.hit_notes:
        if note.kind in (NoteKind.DON, NoteKind.KA):
            assert _note_radius(note, rect, DEFAULT_THEME) == base_r


def test_big_notes_much_larger_than_small():
    _, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    m4 = course.measures[3]
    layout = compute_layout(course, DEFAULT_THEME)
    rect = layout.rows[0][3]
    small_r = _note_radius(
        next(n for n in m4.hit_notes if n.kind == NoteKind.DON), rect, DEFAULT_THEME
    )
    big_r = _note_radius(
        next(n for n in m4.hit_notes if n.kind == NoteKind.BIG_DON), rect, DEFAULT_THEME
    )
    assert big_r >= small_r * 1.35


def test_slot_zero_on_measure_barline():
    _, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    m1 = course.measures[0]
    layout = compute_layout(course, DEFAULT_THEME)
    rect = layout.rows[0][0]
    n = len(m1.slots)
    first = next(n for n in m1.hit_notes if n.slot == 0)
    cx = rect.slot_x(first.slot, n)
    assert abs(cx - rect.x) < 1


def test_consecutive_slots_overlap_on_grid_lines():
    """Dense notes: same radius, grid spacing < diameter → overlap."""
    from fumen.model import Course, Measure

    dense = Course(
        course_id=0,
        measures=[Measure(index=1, slots=list("11" * 12))],
    )
    layout = compute_layout(dense, DEFAULT_THEME)
    rect = layout.rows[0][0]
    n = len(dense.measures[0].slots)
    slot_w = rect.width / n
    d = DEFAULT_THEME.note_diameter
    assert d > slot_w * 1.1


def test_triple_don_parses_three_hits():
    _, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    m1 = course.measures[0]
    assert "".join(m1.slots) == "111"
    kinds = [n.kind for n in sorted(m1.hit_notes, key=lambda n: n.slot)]
    assert kinds == [NoteKind.DON, NoteKind.DON, NoteKind.DON]


def test_don_don_ka_parses_pattern():
    _, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    m2 = course.measures[1]
    assert "".join(m2.slots) == "112"
    kinds = [n.kind for n in sorted(m2.hit_notes, key=lambda n: n.slot)]
    assert kinds == [NoteKind.DON, NoteKind.DON, NoteKind.KA]


def test_sixteen_dons_overlap_geometry():
    """High-density measure: slot pitch narrower than note diameter."""
    _, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    m3 = course.measures[2]
    assert len(m3.hit_notes) == 16
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=300)
    rect = _measure_rect(layout, 3)
    centers = _hit_centers(rect, m3)
    diameter = DEFAULT_THEME.note_diameter
    for left, right in zip(centers, centers[1:]):
        assert right - left < diameter


def test_triple_don_dense_overlap_geometry():
    """Three successive dons in a 16-slot measure (high-BPM style density)."""
    _, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    m4 = course.measures[3]
    assert [n.kind for n in m4.hit_notes] == [NoteKind.DON] * 3
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=300)
    rect = _measure_rect(layout, 4)
    centers = _hit_centers(rect, m4)
    assert len(centers) == 3
    assert centers[1] - centers[0] < DEFAULT_THEME.note_diameter
    assert centers[2] - centers[1] < DEFAULT_THEME.note_diameter


def test_don_don_ka_dense_overlap_geometry():
    _, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    m5 = course.measures[4]
    kinds = [n.kind for n in sorted(m5.hit_notes, key=lambda n: n.slot)]
    assert kinds == [NoteKind.DON, NoteKind.DON, NoteKind.KA]
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=300)
    rect = _measure_rect(layout, 5)
    centers = _hit_centers(rect, m5)
    assert centers[1] - centers[0] < DEFAULT_THEME.note_diameter


def test_triple_don_dense_render_overlap(tmp_path: Path):
    """Rendered dons overlap: midpoint between first two hits is don-colored."""
    song, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    out = tmp_path / "dense.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    m4 = course.measures[3]
    rect = _measure_rect(layout, 4)
    cy = int(rect.y + rect.height / 2)
    centers = _hit_centers(rect, m4)
    mid_x = int((centers[0] + centers[1]) / 2)
    assert img.getpixel((mid_x, cy)) == DEFAULT_THEME.don


def test_don_don_ka_render_colors(tmp_path: Path):
    """Don don ka: first two hits red, third blue (wide spacing, no overlap)."""
    song, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    out = tmp_path / "ddk.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    m2 = course.measures[1]
    rect = _measure_rect(layout, 2)
    cy = int(rect.y + rect.height / 2)
    r = _note_radius(m2.hit_notes[0], rect, DEFAULT_THEME)
    fill_inset = DEFAULT_THEME.note_outline_outer_width + DEFAULT_THEME.note_outline_inner_width
    for note, color in zip(
        sorted(m2.hit_notes, key=lambda n: n.slot),
        [DEFAULT_THEME.don, DEFAULT_THEME.don, DEFAULT_THEME.ka],
    ):
        cx = int(rect.slot_x(note.slot, len(m2.slots)) + fill_inset + 1)
        assert img.getpixel((cx, cy)) == color


def test_don_don_ka_dense_render_overlap(tmp_path: Path):
    """Dense don don ka: midpoint between first two dons is don-colored."""
    song, course = parse_tja(FIXTURES / "dense_patterns.tja", course=0)
    out = tmp_path / "ddk_dense.png"
    render_fumen(song, course, out, width=816)
    img = Image.open(out).convert("RGB")
    layout = compute_layout(course, DEFAULT_THEME, initial_bpm=song.bpm)
    m5 = course.measures[4]
    rect = _measure_rect(layout, 5)
    cy = int(rect.y + rect.height / 2)
    centers = _hit_centers(rect, m5)
    mid_x = int((centers[0] + centers[1]) / 2)
    assert img.getpixel((mid_x, cy)) == DEFAULT_THEME.don
    ka_x = int(centers[2] + 3)
    assert img.getpixel((ka_x, cy)) == DEFAULT_THEME.ka
