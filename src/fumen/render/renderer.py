"""Main render orchestration."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from fumen.model import Course, Song
from fumen.layout.geometry import compute_layout
from fumen.render.canvas import create_canvas
from fumen.render.lane import draw_lanes
from fumen.render.notes_draw import draw_notes
from fumen.theme import DEFAULT_THEME, Theme, scale_theme


def render_fumen(
    song: Song,
    course: Course,
    output: str | Path,
    *,
    theme: Theme | None = None,
    width: int | None = None,
    font_path: str | None = None,
) -> Path:
    base = theme or DEFAULT_THEME
    if width:
        base = scale_theme(base, width)
    layout = compute_layout(course, base, initial_bpm=song.bpm)
    img, draw = create_canvas(layout, base)
    draw_lanes(draw, layout, base, font_path)
    draw_notes(draw, layout, base, font_path)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, format="PNG")
    return out
