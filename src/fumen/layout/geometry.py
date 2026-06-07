"""Pixel geometry for chart layout."""

from __future__ import annotations

from dataclasses import dataclass

from fumen.model import Course, Measure
from fumen.layout.paginate import paginate_measures
from fumen.theme import Theme


@dataclass(frozen=True)
class MeasureRect:
    measure: Measure
    x: int
    y: int
    width: int
    height: int
    row_index: int
    col_index: int
    header_y: int

    def slot_x(self, slot: int, num_slots: int) -> float:
        if num_slots <= 0:
            return float(self.x)
        return self.x + (slot / num_slots) * self.width

@dataclass
class Layout:
    rows: list[list[MeasureRect]]
    header_height: int
    content_height: int
    content_width: int
    page_height: int
    page_width: int
    initial_bpm: float


def compute_layout(
    course: Course,
    theme: Theme,
    *,
    initial_bpm: float = 120.0,
) -> Layout:
    measure_rows = paginate_measures(course.measures, theme.measures_per_row)
    bleed = theme.track_bleed_x
    chart_width = theme.measure_width * theme.measures_per_row
    content_width = theme.page_padding_x * 2 + chart_width + bleed * 2
    chart_top = theme.page_padding_top
    page_width = content_width

    rows: list[list[MeasureRect]] = []
    lane_y = chart_top
    for ri, mrow in enumerate(measure_rows):
        if ri == 0:
            header_y = chart_top
            lane_y = header_y + theme.row_header_height
        else:
            prev = rows[ri - 1][0]
            # Page-coloured gap after lane, then next row header.
            header_y = prev.y + prev.height + theme.row_gap
            lane_y = header_y + theme.row_header_height
        row_rects: list[MeasureRect] = []
        for ci, measure in enumerate(mrow):
            x = theme.page_padding_x + bleed + ci * theme.measure_width
            row_rects.append(
                MeasureRect(
                    measure=measure,
                    x=x,
                    y=lane_y,
                    width=theme.measure_width,
                    height=theme.lane_height,
                    row_index=ri,
                    col_index=ci,
                    header_y=header_y,
                )
            )
        rows.append(row_rects)

    if rows:
        last = rows[-1][0]
        content_height = last.y + last.height - chart_top
    else:
        content_height = 0
    page_height = chart_top + content_height + theme.page_padding_bottom

    return Layout(
        rows=rows,
        header_height=chart_top,
        content_height=content_height,
        content_width=content_width,
        page_height=page_height,
        page_width=page_width,
        initial_bpm=initial_bpm,
    )
