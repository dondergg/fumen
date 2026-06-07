"""Render smoke tests."""

from pathlib import Path

from fumen.render.renderer import render_fumen
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_render_png(tmp_path: Path):
    song, course = parse_tja(FIXTURES / "simple.tja")
    out = tmp_path / "out.png"
    render_fumen(song, course, out, width=800)
    assert out.exists()
    assert out.stat().st_size > 1000
