"""BPM label shows chart start BPM, not row tail."""

from pathlib import Path

from PIL import Image

from fumen.render.renderer import render_fumen
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def _bpm_header_crop(img: Image.Image, layout, measure_index: int = 1) -> tuple:
    rect = _measure_rect(layout, measure_index)
    cy = rect.header_y + (rect.y - rect.header_y) // 2
    x0 = rect.x + 45
    crop = img.crop((x0, cy - 5, x0 + 70, cy + 6))
    return tuple(crop.get_flattened_data())


def _measure_rect(layout, measure_index: int):
    for row in layout.rows:
        for rect in row:
            if rect.measure.index == measure_index:
                return rect
    raise KeyError(measure_index)


def test_bpm_row_shows_170_not_200(tmp_path: Path):
    """Row has BPMCHANGE 200 in m2; m1 label must still read BPM 170."""
    from fumen.layout.geometry import compute_layout
    from fumen.theme import DEFAULT_THEME

    song_row, course_row = parse_tja(FIXTURES / "bpm_row.tja", course=0)
    assert song_row.bpm == 170
    assert course_row.measures[1].bpm == 200

    song_170, course_170 = parse_tja(FIXTURES / "bpm_170.tja", course=0)
    song_200, course_200 = parse_tja(FIXTURES / "bpm_200.tja", course=0)

    row_out = tmp_path / "row.png"
    render_fumen(song_row, course_row, row_out, width=816)
    row_img = Image.open(row_out).convert("RGB")
    row_layout = compute_layout(course_row, DEFAULT_THEME, initial_bpm=song_row.bpm)

    out_170 = tmp_path / "bpm170.png"
    render_fumen(song_170, course_170, out_170, width=816)
    img_170 = Image.open(out_170).convert("RGB")
    layout_170 = compute_layout(course_170, DEFAULT_THEME, initial_bpm=song_170.bpm)

    out_200 = tmp_path / "bpm200.png"
    render_fumen(song_200, course_200, out_200, width=816)
    img_200 = Image.open(out_200).convert("RGB")
    layout_200 = compute_layout(course_200, DEFAULT_THEME, initial_bpm=song_200.bpm)

    crop_row = _bpm_header_crop(row_img, row_layout)
    crop_170 = _bpm_header_crop(img_170, layout_170)
    crop_200 = _bpm_header_crop(img_200, layout_200)

    assert crop_row == crop_170
    assert crop_row != crop_200


def test_bpm_change_shows_on_changed_measure(tmp_path: Path):
    """BPM label appears on the measure where BPMCHANGE takes effect."""
    from fumen.layout.geometry import compute_layout
    from fumen.theme import DEFAULT_THEME

    song_row, course_row = parse_tja(FIXTURES / "bpm_row.tja", course=0)
    _, course_200 = parse_tja(FIXTURES / "bpm_200.tja", course=0)

    row_out = tmp_path / "row.png"
    render_fumen(song_row, course_row, row_out, width=816)
    row_img = Image.open(row_out).convert("RGB")
    row_layout = compute_layout(course_row, DEFAULT_THEME, initial_bpm=song_row.bpm)

    out_200 = tmp_path / "bpm200.png"
    render_fumen(song_row, course_200, out_200, width=816)
    img_200 = Image.open(out_200).convert("RGB")
    layout_200 = compute_layout(course_200, DEFAULT_THEME, initial_bpm=200)

    crop_m2 = _bpm_header_crop(row_img, row_layout, measure_index=2)
    crop_200 = _bpm_header_crop(img_200, layout_200)
    crop_170 = _bpm_header_crop(row_img, row_layout, measure_index=1)

    assert crop_m2 == crop_200
    assert crop_m2 != crop_170
