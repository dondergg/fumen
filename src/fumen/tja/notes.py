"""Resolve slot characters into hit notes and span notes."""

from __future__ import annotations

from fumen.model import Course, Measure, NoteKind, SlotNote, SpanNote

Pending = tuple[int, NoteKind]


def char_to_kind(ch: str) -> NoteKind | None:
    c = ch.upper()
    mapping = {
        "1": NoteKind.DON,
        "A": NoteKind.DON,
        "2": NoteKind.KA,
        "B": NoteKind.KA,
        "3": NoteKind.BIG_DON,
        "4": NoteKind.BIG_KA,
        "5": NoteKind.ROLL,
        "6": NoteKind.BIG_ROLL,
        "7": NoteKind.BALLOON,
        "9": NoteKind.BIG_BALLOON,
    }
    return mapping.get(c)


def is_head(ch: str) -> bool:
    return ch.upper() in "5679"


def is_tail(ch: str) -> bool:
    return ch == "8"


def _pop_balloon(balloons: list[int], kind: NoteKind) -> int | None:
    if kind in (NoteKind.BALLOON, NoteKind.BIG_BALLOON):
        return balloons.pop(0) if balloons else 1
    return None


def _append_span(
    measure: Measure,
    start: int,
    end: int,
    kind: NoteKind,
    balloons: list[int],
    *,
    continues_to_next: bool = False,
    continues_from_prev: bool = False,
) -> list[int]:
    hits = _pop_balloon(balloons, kind)
    measure.span_notes.append(
        SpanNote(
            start_slot=start,
            end_slot=end,
            kind=kind,
            balloon_hits=hits,
            continues_to_next=continues_to_next,
            continues_from_prev=continues_from_prev,
        )
    )
    return balloons


def finalize_course_notes(course: Course, branch_balloons: list[int]) -> None:
    """Resolve hit/span notes for all measures, including cross-measure rolls."""
    balloons = list(branch_balloons)
    pending: Pending | None = None
    pending_measure: Measure | None = None

    for measure in course.measures:
        if pending is not None and pending_measure is not None:
            tail_idx = next((i for i, ch in enumerate(measure.slots) if ch == "8"), None)
            if tail_idx is not None:
                _, kind = pending
                # pending_measure already got continues_to_next at previous measure end
                balloons = _append_span(
                    measure,
                    0,
                    tail_idx,
                    kind,
                    balloons,
                    continues_from_prev=True,
                )
                pending = None
                pending_measure = None

        i = 0
        while i < len(measure.slots):
            ch = measure.slots[i]

            # Tail (8) before char_to_kind — 8 is not a hit digit
            if is_tail(ch):
                if pending is not None and pending_measure is not None:
                    start_slot, pkind = pending
                    balloons = _append_span(
                        pending_measure, start_slot, i, pkind, balloons
                    )
                    pending = None
                    pending_measure = None
                i += 1
                continue

            if ch in "0fF":
                i += 1
                continue

            if is_head(ch):
                kind = char_to_kind(ch)
                if kind is None:
                    i += 1
                    continue
                if pending is not None and pending_measure is not None:
                    start_slot, pkind = pending
                    balloons = _append_span(
                        pending_measure, start_slot, i - 1, pkind, balloons
                    )
                pending = (i, kind)
                pending_measure = measure
                i += 1
                continue

            kind = char_to_kind(ch)
            if kind is None:
                i += 1
                continue

            if kind in (NoteKind.DON, NoteKind.KA, NoteKind.BIG_DON, NoteKind.BIG_KA):
                measure.hit_notes.append(SlotNote(slot=i, kind=kind))
            i += 1

        if pending is not None and pending_measure is not None:
            start_slot, kind = pending
            balloons = _append_span(
                pending_measure,
                start_slot,
                len(pending_measure.slots) - 1,
                kind,
                balloons,
                continues_to_next=True,
            )
            # keep pending for roll/balloon continuing on the next measure
