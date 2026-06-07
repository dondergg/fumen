"""Cross-measure drumrolls render as one connected span."""

from pathlib import Path

from fumen.model import NoteKind
from fumen.tja.parser import parse_tja

FIXTURES = Path(__file__).parent / "fixtures"


def test_cross_measure_roll_spans_measures():
    _, course = parse_tja(FIXTURES / "cross_measure.tja", course=0)
    m1, m2 = course.measures[0], course.measures[1]
    assert len(m1.span_notes) == 1
    roll1 = m1.span_notes[0]
    assert roll1.kind == NoteKind.ROLL
    assert roll1.continues_to_next
    rolls2 = [s for s in m2.span_notes if s.kind == NoteKind.ROLL]
    assert len(rolls2) == 1
    assert rolls2[0].continues_from_prev
