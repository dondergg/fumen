"""Layout tests."""

from pathlib import Path

from fumen.layout.geometry import compute_layout
from fumen.layout.paginate import paginate_measures
from fumen.theme import DEFAULT_THEME
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_paginate():
    _, course = parse_tja(FIXTURES / "simple.tja")
    rows = paginate_measures(course.measures, 4)
    assert len(rows) == 2
    assert len(rows[0]) == 4


def test_compute_layout():
    _, course = parse_tja(FIXTURES / "simple.tja")
    layout = compute_layout(course, DEFAULT_THEME)
    assert layout.page_height > 0
    assert len(layout.rows) >= 1
