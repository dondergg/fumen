"""Remove non-playable trailing measures from parsed courses."""

from __future__ import annotations

from fumen.model import Course, Measure

# Chart padding after the song ends (empty slots, barline flags, scroll, etc.)
_PADDING_EVENTS = frozenset(
    {
        "BARLINEOFF",
        "BARLINEON",
        "SCROLL",
        "HSPEED",
        "HBSCROLL",
        "BMSCROLL",
    }
)


def is_trailing_padding_measure(measure: Measure) -> bool:
    """True when a measure has no notes and only end-of-chart filler."""
    if measure.hit_notes or measure.span_notes:
        return False
    if any(slot != "0" for slot in measure.slots):
        return False
    for event in measure.events:
        if event.name not in _PADDING_EVENTS:
            return False
    return True


def strip_trailing_padding_measures(course: Course) -> int:
    """Drop extra trailing padding; keep one tail measure visible (e.g. empty m82)."""
    removed = 0
    while (
        len(course.measures) >= 2
        and is_trailing_padding_measure(course.measures[-1])
        and is_trailing_padding_measure(course.measures[-2])
    ):
        course.measures.pop()
        removed += 1
    return removed
