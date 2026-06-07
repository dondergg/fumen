"""Tail digit 8 must close rolls and balloons."""

from pathlib import Path

from fumen.model import NoteKind
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_showcase_balloon_span():
    _, course = parse_tja(FIXTURES / "showcase.tja", course=0)
    m8 = course.measures[7]
    balloons = [s for s in m8.span_notes if s.kind == NoteKind.BALLOON]
    assert len(balloons) == 1
    assert balloons[0].balloon_hits == 8


def test_roll_tail_closes():
    from fumen.model import Course, Measure
    from fumen.tja.notes import finalize_course_notes

    m = Measure(index=1, slots=list("500080"))
    course = Course(course_id=0, measures=[m])
    finalize_course_notes(course, [])
    assert len(m.span_notes) == 1
    assert m.span_notes[0].end_slot == 4
