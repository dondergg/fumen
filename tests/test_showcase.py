from pathlib import Path

from fumen.render.renderer import render_fumen
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_showcase_render(tmp_path: Path):
    song, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    assert song.title.startswith("コドモ")
    assert len(course.measures) >= 10
    out = tmp_path / "showcase.png"
    render_fumen(song, course, out, width=1280)
    assert out.stat().st_size > 5000
