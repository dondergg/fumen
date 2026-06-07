"""Draw note glyphs on lanes."""

from __future__ import annotations

from PIL import ImageDraw

from fumen.layout.geometry import Layout, MeasureRect
from fumen.model import Measure, NoteKind, SpanNote, SlotNote
from fumen.render.canvas import _load_font, draw_text_centered
from fumen.theme import Theme

_BALLOON_KINDS = frozenset({NoteKind.BALLOON, NoteKind.BIG_BALLOON})


def _note_color(kind: NoteKind, theme: Theme) -> tuple[int, int, int]:
    if kind in (NoteKind.DON, NoteKind.BIG_DON):
        return theme.don
    if kind in (NoteKind.KA, NoteKind.BIG_KA):
        return theme.ka
    if kind in (NoteKind.ROLL, NoteKind.BIG_ROLL):
        return theme.roll
    return theme.balloon


def _balloon_head_radius(*, big: bool, theme: Theme) -> int:
    """Balloon head matches small/big don size; tail bar is drawn separately."""
    diameter = theme.big_note_diameter if big else theme.note_diameter
    fill_r = max(4, diameter // 2 - 2)
    return fill_r + theme.note_outline_outer_width + theme.note_outline_inner_width


def _roll_fill_height(*, big: bool, theme: Theme) -> int:
    """Roll outer height matches small/big don-ka diameter (outline included)."""
    diameter = theme.big_note_diameter if big else theme.note_diameter
    outline = 2 * (theme.note_outline_outer_width + theme.note_outline_inner_width)
    return max(1, diameter - outline)


def _note_radius(note: SlotNote, rect: MeasureRect, theme: Theme) -> int:
    """One fixed size per class: small don/ka vs big don/ka (TJA 3/4)."""
    max_r = int(rect.height / 2 - 1)
    big = note.kind in (NoteKind.BIG_DON, NoteKind.BIG_KA)
    diameter = theme.big_note_diameter if big else theme.note_diameter
    return min(diameter // 2, max_r)


def _draw_circle(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
    outline_width: int,
) -> None:
    if radius <= 0:
        return
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=fill,
        outline=outline,
        width=outline_width,
    )


def _draw_donka_circle(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: int,
    fill: tuple[int, int, int],
    theme: Theme,
) -> None:
    """Don/ka: black outer ring, white inner ring, then fill."""
    if radius <= 0:
        return
    ow = theme.note_outline_outer_width
    iw = theme.note_outline_inner_width
    if radius <= ow + iw:
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=fill,
        )
        return
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=theme.note_outline_outer,
    )
    r_white = radius - ow
    draw.ellipse(
        [cx - r_white, cy - r_white, cx + r_white, cy + r_white],
        fill=theme.note_outline,
    )
    r_fill = radius - ow - iw
    draw.ellipse(
        [cx - r_fill, cy - r_fill, cx + r_fill, cy + r_fill],
        fill=fill,
    )


def _draw_pill_fill(
    draw: ImageDraw.ImageDraw,
    x0: float,
    x1: float,
    y: float,
    height: int,
    fill: tuple[int, int, int],
    *,
    round_left: bool = True,
    round_right: bool = True,
) -> None:
    """Filled pill bar without outline."""
    if height <= 0:
        return
    if x1 < x0:
        x0, x1 = x1, x0
    r = height // 2
    top = y - r
    bot = y + r
    min_w = 2 * r if round_left and round_right else r
    if x1 - x0 < min_w:
        x1 = x0 + min_w

    body_l = x0 + (r if round_left else 0)
    body_r = x1 - (r if round_right else 0)
    if body_r > body_l:
        draw.rectangle([body_l, top, body_r, bot], fill=fill)
    if round_left:
        draw.ellipse([x0, top, x0 + 2 * r, bot], fill=fill)
    if round_right:
        draw.ellipse([x1 - 2 * r, top, x1, bot], fill=fill)


def _draw_outlined_pill_bar(
    draw: ImageDraw.ImageDraw,
    x0: float,
    x1: float,
    y: float,
    fill_height: int,
    fill: tuple[int, int, int],
    theme: Theme,
    *,
    round_left: bool = True,
    round_right: bool = True,
) -> None:
    """Pill bar with black outer ring and white inner ring (don/ka style)."""
    ow = theme.note_outline_outer_width
    iw = theme.note_outline_inner_width
    outer_h = fill_height + 2 * (ow + iw)
    if outer_h <= 0:
        return

    cap = {"round_left": round_left, "round_right": round_right}
    _draw_pill_fill(
        draw, x0, x1, y, outer_h, theme.note_outline_outer, **cap,
    )

    white_h = outer_h - 2 * ow
    if white_h > 0:
        _draw_pill_fill(
            draw,
            x0 + (ow if round_left else 0),
            x1 - (ow if round_right else 0),
            y,
            white_h,
            theme.note_outline,
            **cap,
        )

    inner_h = outer_h - 2 * (ow + iw)
    if inner_h > 0:
        _draw_pill_fill(
            draw,
            x0 + (ow + iw if round_left else 0),
            x1 - (ow + iw if round_right else 0),
            y,
            inner_h,
            fill,
            **cap,
        )


def _continuation_partner(measure: Measure, kind: NoteKind) -> SpanNote | None:
    for span in measure.span_notes:
        if span.continues_from_prev and span.kind == kind:
            return span
    return None


def _next_measure_rect(
    rows: list[list[MeasureRect]],
    row_index: int,
    col_index: int,
) -> MeasureRect | None:
    row = rows[row_index]
    if col_index + 1 < len(row):
        return row[col_index + 1]
    if row_index + 1 < len(rows) and rows[row_index + 1]:
        return rows[row_index + 1][0]
    return None


def _span_end_x(rect: MeasureRect, span: SpanNote) -> float:
    n = len(rect.measure.slots) or 1
    return rect.slot_x(span.end_slot + 1, n) - 1


def _span_start_x(rect: MeasureRect, span: SpanNote) -> float:
    n = len(rect.measure.slots) or 1
    return rect.slot_x(span.start_slot, n)


def _draw_span_bar(
    draw: ImageDraw.ImageDraw,
    x0: float,
    x1: float,
    cy: float,
    span: SpanNote,
    theme: Theme,
    font_path: str | None,
    *,
    round_left: bool,
    round_right: bool,
) -> None:
    cap = {"round_left": round_left, "round_right": round_right}
    if span.kind in _BALLOON_KINDS:
        big = span.kind == NoteKind.BIG_BALLOON
        bar_h = (
            _roll_fill_height(big=True, theme=theme)
            if big
            else theme.balloon_bar_height
        )
        if round_left:
            head_r = _balloon_head_radius(big=big, theme=theme)
            cx = x0 + head_r
            # Tail from head center (50%); circle paints on top — no left-edge bar slivers.
            if x1 > cx:
                _draw_outlined_pill_bar(
                    draw, cx, x1, cy, bar_h,
                    theme.balloon_bar, theme,
                    round_left=False, round_right=round_right,
                )
            _draw_donka_circle(draw, cx, cy, head_r, theme.balloon, theme)
            if span.balloon_hits is not None:
                font = _load_font(theme.font_size_meta, font_path)
                draw_text_centered(
                    draw, cx, cy, str(span.balloon_hits), font, theme.balloon_text
                )
        else:
            _draw_outlined_pill_bar(
                draw, x0, x1, cy, bar_h,
                theme.balloon_bar, theme, **cap,
            )
    else:
        big = span.kind == NoteKind.BIG_ROLL
        _draw_outlined_pill_bar(
            draw, x0, x1, cy, _roll_fill_height(big=big, theme=theme),
            theme.roll, theme, **cap,
        )


def _draw_merged_span(
    draw: ImageDraw.ImageDraw,
    start_rect: MeasureRect,
    start_span: SpanNote,
    end_rect: MeasureRect,
    end_span: SpanNote,
    theme: Theme,
    font_path: str | None,
) -> None:
    """One continuous bar across measures — rounded only at the true ends."""
    cy = start_rect.y + start_rect.height / 2
    x0 = _span_start_x(start_rect, start_span)
    x1 = _span_end_x(end_rect, end_span)
    _draw_span_bar(
        draw, x0, x1, cy, start_span, theme, font_path,
        round_left=True, round_right=True,
    )


def draw_notes_for_row(
    draw: ImageDraw.ImageDraw,
    row: list[MeasureRect],
    row_index: int,
    all_rows: list[list[MeasureRect]],
    theme: Theme,
    font_path: str | None = None,
) -> None:
    skip: set[int] = set()

    for col_index, rect in enumerate(row):
        measure = rect.measure
        num_slots = len(measure.slots) or 1
        cy = rect.y + rect.height / 2
        for span in measure.span_notes:
            if id(span) in skip:
                continue

            if span.continues_to_next:
                next_rect = _next_measure_rect(all_rows, row_index, col_index)
                if next_rect is not None:
                    partner = _continuation_partner(next_rect.measure, span.kind)
                    if partner is not None:
                        _draw_merged_span(
                            draw, rect, span, next_rect, partner, theme, font_path
                        )
                        skip.add(id(partner))
                        continue

            x0 = _span_start_x(rect, span)
            x1 = _span_end_x(rect, span)
            _draw_span_bar(
                draw, x0, x1, cy, span, theme, font_path,
                round_left=not span.continues_from_prev,
                round_right=not span.continues_to_next,
            )

        for note in sorted(measure.hit_notes, key=lambda n: n.slot):
            cx = rect.slot_x(note.slot, num_slots)
            r = _note_radius(note, rect, theme)
            color = _note_color(note.kind, theme)
            if note.kind in (NoteKind.DON, NoteKind.KA, NoteKind.BIG_DON, NoteKind.BIG_KA):
                _draw_donka_circle(draw, cx, cy, r, color, theme)
            else:
                _draw_circle(
                    draw, cx, cy, r, color, theme.note_outline, theme.note_outline_width
                )


def draw_notes_on_measure(
    draw: ImageDraw.ImageDraw,
    rect: MeasureRect,
    theme: Theme,
    font_path: str | None = None,
) -> None:
    """Draw notes for a single measure (no cross-measure merge)."""
    draw_notes_for_row(draw, [rect], 0, [[rect]], theme, font_path)


def draw_notes(
    draw: ImageDraw.ImageDraw,
    layout: Layout,
    theme: Theme,
    font_path: str | None = None,
) -> None:
    for row_index, row in enumerate(layout.rows):
        draw_notes_for_row(draw, row, row_index, layout.rows, theme, font_path)
