"""Parser unit tests."""

from pathlib import Path

import pytest

from fumen.model import BranchPath, NoteKind
from fumen.tja.parser import ParseError, parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_simple_parse():
    song, course = parse_tja(FIXTURES / "simple.tja", course=0)
    assert song.title == "Test Song"
    assert song.subtitle == "Test Artist"
    assert len(course.measures) == 5
    assert course.measures[0].bpm == 130.0
    gogo = [m for m in course.measures if m.gogo]
    assert len(gogo) >= 1
    assert any(n.kind == NoteKind.DON for m in course.measures for n in m.hit_notes)


def test_balloon_span():
    song, course = parse_tja(FIXTURES / "simple.tja", course=0)
    balloons = [
        s for m in course.measures for s in m.span_notes if s.kind == NoteKind.BALLOON
    ]
    assert len(balloons) >= 1
    assert balloons[0].balloon_hits == 5


def test_multi_course():
    song, easy = parse_tja(FIXTURES / "multi_course.tja", course=0)
    assert len(easy.measures) == 1
    _, oni = parse_tja(FIXTURES / "multi_course.tja", course=3)
    assert len(oni.measures) == 2


def test_branch_normal():
    _, course = parse_tja(
        FIXTURES / "branch.tja", course=0, branch=BranchPath.NORMAL
    )
    assert len(course.measures) >= 2


def test_branch_advanced():
    _, course = parse_tja(
        FIXTURES / "branch.tja", course=0, branch=BranchPath.ADVANCED
    )
    slots = "".join("".join(m.slots) for m in course.measures)
    assert "2" in slots


def test_missing_course():
    with pytest.raises(ParseError):
        parse_tja(FIXTURES / "simple.tja", course=99)


def test_cross_measure_roll():
    _, course = parse_tja(FIXTURES / "cross_measure.tja")
    assert len(course.measures) == 2
    assert course.measures[0].span_notes[0].continues_to_next
    assert course.measures[1].span_notes[0].continues_from_prev
    assert course.measures[1].span_notes[0].end_slot == 1  # tail at slot 1 in "08"
