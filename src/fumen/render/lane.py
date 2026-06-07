"""Draw measure lanes, grid, and labels."""

from __future__ import annotations

from PIL import ImageDraw

from fumen.layout.geometry import Layout, MeasureRect
from fumen.render.canvas import _load_font, draw_text_left_middle
from fumen.model import Measure
from fumen.theme import Theme


def _gogo_x_range(rect: MeasureRect) -> tuple[float, float] | None:
    """Horizontal [x0, x1) span of gogo salmon in a measure header."""
    measure = rect.measure
    if not measure.gogo:
        return None
    n = len(measure.slots) or 1
    if measure.gogo_start_slot is not None:
        x0 = rect.slot_x(measure.gogo_start_slot, n)
        end = (
            measure.gogo_end_slot
            if measure.gogo_end_slot is not None
            else n - 1
        )
        x1 = rect.slot_x(end + 1, n)
        return x0, x1
    return float(rect.x), float(rect.x + rect.width)


def _header_fill_at(rect: MeasureRect, x: float, theme: Theme) -> tuple[int, int, int]:
    rng = _gogo_x_range(rect)
    if rng is None:
        return theme.row_header
    x0, x1 = rng
    if x0 <= x < x1:
        return theme.row_header_gogo
    return theme.row_header


def _measure_header_fill(rect: MeasureRect, label_x: float, theme: Theme) -> tuple[int, int, int]:
    return _header_fill_at(rect, label_x, theme)


def _draw_measure_header_label(
    draw: ImageDraw.ImageDraw,
    *,
    barline_x: int,
    label_x: float,
    header_y: int,
    header_h: int,
    header_cy: int,
    text: str,
    font,
    theme: Theme,
    header_fill: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    """Header backing right of the barline through the label (barline stays full height)."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    pad_x = 3
    bg_bottom = header_y + header_h - 1
    bg_left = barline_x + theme.measure_divider_width
    bg = [
        bg_left,
        header_y,
        int(label_x) + tw + pad_x,
        bg_bottom,
    ]
    draw.rectangle(bg, fill=header_fill)
    return draw_text_left_middle(
        draw, label_x, header_cy, text, font, theme.measure_number
    )


def _format_bpm(bpm: float) -> str:
    if abs(bpm - round(bpm)) < 0.05:
        return f"BPM {int(round(bpm))}"
    return f"BPM {bpm:.1f}"


def _measure_shows_bpm(measure: Measure, prev_bpm: float | None) -> bool:
    bpm = measure.bpm
    if bpm is None:
        return False
    if measure.index == 1:
        return True
    if prev_bpm is None:
        return True
    return abs(bpm - prev_bpm) > 0.01


def _draw_lane_gogo(
    draw: ImageDraw.ImageDraw,
    rect: MeasureRect,
    theme: Theme,
) -> None:
    """Salmon lane interior for full or partial gogo spans."""
    rng = _gogo_x_range(rect)
    if rng is None:
        return
    y0 = rect.y
    y1 = _lane_bottom_y(y0, rect.height)
    iy0, iy1 = _lane_inner_y(y0, y1, theme)
    if iy1 <= iy0:
        return
    x0 = int(rng[0])
    x1 = max(x0 + 1, int(rng[1]))
    draw.rectangle([x0, iy0, x1 - 1, iy1], fill=theme.lane_gogo)


def _row_extent(row: list[MeasureRect]) -> tuple[int, int, int, int]:
    x0 = row[0].x
    x1 = row[-1].x + row[-1].width
    y0 = row[0].header_y
    y1 = row[0].y + row[0].height
    return x0, y0, x1, y1


def _draw_row_headers(
    draw: ImageDraw.ImageDraw,
    row: list[MeasureRect],
    *,
    track_x0: int,
    track_x1: int,
    header_y: int,
    header_h: int,
    theme: Theme,
) -> None:
    """Header band on top of lane art so grid/barlines cannot bleed into salmon/grey."""
    header_bottom = header_y + header_h - 1
    draw.rectangle(
        [track_x0, header_y, track_x1, header_bottom],
        fill=theme.row_header,
    )
    for rect in row:
        rng = _gogo_x_range(rect)
        if rng is None:
            continue
        x0, x1 = int(rng[0]), max(int(rng[0]) + 1, int(rng[1]))
        draw.rectangle(
            [x0, header_y, x1 - 1, header_bottom],
            fill=theme.row_header_gogo,
        )


def _lane_band_bounds(
    y0: int, y1: int, theme: Theme
) -> tuple[int, int, int, int] | None:
    """Top/bottom white accent band Y bounds inside lane (None if lane too thin)."""
    bw = theme.lane_border_width
    aw = theme.lane_border_accent_width
    if aw <= 0 or bw <= 0:
        return None
    top_black_bot = y0 + bw - 1
    top_white_bot = top_black_bot + aw
    bot_black_top = y1 - bw + 1
    bot_white_top = bot_black_top - aw
    if top_white_bot >= bot_white_top:
        return None
    return top_black_bot, top_white_bot, bot_black_top, bot_white_top


def _lane_inner_y(y0: int, y1: int, theme: Theme) -> tuple[int, int]:
    """Grey lane interior between white accent bands."""
    inset = theme.lane_border_width + theme.lane_border_accent_width
    inner_y0 = y0 + inset
    inner_y1 = y1 - inset
    return inner_y0, max(inner_y0, inner_y1)


def _draw_lane_grid(
    draw: ImageDraw.ImageDraw,
    rect: MeasureRect,
    theme: Theme,
) -> None:
    measure = rect.measure
    num_slots = len(measure.slots) or 1
    x0 = rect.x
    x1 = rect.x + rect.width
    y0 = rect.y
    y1 = _lane_bottom_y(y0, rect.height)
    iy0, iy1 = _lane_inner_y(y0, y1, theme)
    if iy1 <= iy0:
        return

    # Single centre staff line
    ly = int((iy0 + iy1) / 2)
    draw.line([(x0, ly), (x1, ly)], fill=theme.lane_line, width=1)

    # Vertical subdivisions at every slot; measure edges drawn separately
    if num_slots <= theme.max_grid_slots:
        for s in range(1, num_slots):
            sx = int(rect.slot_x(s, num_slots))
            draw.line([(sx, iy0), (sx, iy1)], fill=theme.grid_line, width=1)


def _redraw_lane_accents(
    draw: ImageDraw.ImageDraw,
    track_x0: int,
    track_x1: int,
    y0: int,
    y1: int,
    theme: Theme,
) -> None:
    """Repaint white accent bands on top of grid/barlines."""
    bands = _lane_band_bounds(y0, y1, theme)
    if bands is None:
        return
    top_black_bot, top_white_bot, bot_black_top, bot_white_top = bands
    draw.rectangle(
        [track_x0, top_black_bot + 1, track_x1, top_white_bot],
        fill=theme.lane_border_accent,
    )
    draw.rectangle(
        [track_x0, bot_white_top, track_x1, bot_black_top - 1],
        fill=theme.lane_border_accent,
    )


def _lane_bottom_y(lane_y0: int, lane_height: int) -> int:
    """Inclusive bottom pixel for a lane of lane_height pixels."""
    return lane_y0 + lane_height - 1


def _draw_row_track(
    draw: ImageDraw.ImageDraw,
    track_x0: int,
    track_x1: int,
    y0: int,
    y1: int,
    theme: Theme,
) -> None:
    """Lane stack: black → white → grey → white → black."""
    bands = _lane_band_bounds(y0, y1, theme)
    if bands is None:
        draw.rectangle([track_x0, y0, track_x1, y1], fill=theme.lane_bg)
        return

    top_black_bot, top_white_bot, bot_black_top, bot_white_top = bands
    bw = theme.lane_border_width
    aw = theme.lane_border_accent_width
    if bw > 0:
        draw.rectangle([track_x0, y0, track_x1, top_black_bot], fill=theme.lane_border)
        draw.rectangle([track_x0, bot_black_top, track_x1, y1], fill=theme.lane_border)
    if aw > 0:
        draw.rectangle(
            [track_x0, top_black_bot + 1, track_x1, top_white_bot],
            fill=theme.lane_border_accent,
        )
        draw.rectangle(
            [track_x0, bot_white_top, track_x1, bot_black_top - 1],
            fill=theme.lane_border_accent,
        )
    draw.rectangle(
        [track_x0, top_white_bot + 1, track_x1, bot_white_top - 1],
        fill=theme.lane_bg,
    )


def _span_bridges_measures(prev: Measure, nxt: Measure) -> bool:
    for span in prev.span_notes:
        if not span.continues_to_next:
            continue
        if any(
            s.continues_from_prev and s.kind == span.kind for s in nxt.span_notes
        ):
            return True
    return False


def _collect_barline_skip_x(
    row: list[MeasureRect],
    row_index: int,
    all_rows: list[list[MeasureRect]],
) -> set[int]:
    """Barlines to omit where a roll/balloon bridges from the previous measure."""
    skip: set[int] = set()
    for ci, rect in enumerate(row):
        if ci == 0:
            if row_index == 0:
                continue
            prev_row = all_rows[row_index - 1]
            if not prev_row:
                continue
            prev = prev_row[-1]
            if _span_bridges_measures(prev.measure, rect.measure):
                skip.add(rect.x)
            continue
        prev = row[ci - 1]
        if _span_bridges_measures(prev.measure, rect.measure):
            skip.add(rect.x)
    return skip


def draw_lanes(
    draw: ImageDraw.ImageDraw,
    layout: Layout,
    theme: Theme,
    font_path: str | None,
    show_bpm_labels: bool = True,
) -> None:
    measure_font = _load_font(theme.font_size_measure, font_path)
    bpm_font = _load_font(theme.font_size_bpm, font_path)
    meta_font = _load_font(theme.font_size_meta, font_path)
    prev_bpm: float | None = None

    for row_index, row in enumerate(layout.rows):
        if not row:
            continue
        x0, y0, x1, y1 = _row_extent(row)
        header_h = row[0].y - row[0].header_y

        lane_y0 = row[0].y
        lane_y1 = _lane_bottom_y(lane_y0, row[0].height)
        header_cy = y0 + header_h // 2
        track_x0 = 0
        track_x1 = layout.page_width
        divider_w = theme.measure_divider_width
        _draw_row_track(draw, track_x0, track_x1, lane_y0, lane_y1, theme)

        for rect in row:
            _draw_lane_gogo(draw, rect, theme)

        for rect in row:
            measure = rect.measure
            for ev in measure.events:
                if ev.name == "HSPEED" and ev.value:
                    try:
                        hs = float(ev.value)
                        draw.text(
                            (
                                rect.x + theme.hs_label_offset_x,
                                rect.header_y + 1,
                            ),
                            f"HS {hs:.2f}".rstrip("0").rstrip("."),
                            fill=theme.hs_label,
                            font=meta_font,
                        )
                    except ValueError:
                        pass

            _draw_lane_grid(draw, rect, theme)

        _redraw_lane_accents(draw, track_x0, track_x1, lane_y0, lane_y1, theme)

        barline_skip_x = _collect_barline_skip_x(row, row_index, layout.rows)

        _draw_row_headers(
            draw,
            row,
            track_x0=track_x0,
            track_x1=track_x1,
            header_y=y0,
            header_h=header_h,
            theme=theme,
        )

        # Measure barlines span header top through lane bottom (labels patch over digits)
        if lane_y1 > y0:
            bar_y0, bar_y1 = y0, lane_y1
            for ci, rect in enumerate(row):
                sx = rect.x
                if ci > 0 and not row[ci - 1].measure.show_barline:
                    continue
                if sx in barline_skip_x:
                    continue
                draw.line(
                    [(sx, bar_y0), (sx, bar_y1)],
                    fill=theme.measure_divider,
                    width=divider_w,
                )
            end_x = row[-1].x + row[-1].width
            if row[-1].measure.show_barline:
                draw.line(
                    [(end_x, bar_y0), (end_x, bar_y1)],
                    fill=theme.measure_divider,
                    width=divider_w,
                )

        label_x_offset = divider_w + theme.measure_number_pad_x
        for rect in row:
            measure = rect.measure
            label = str(measure.index)
            barline_x = rect.x
            label_x = barline_x + label_x_offset
            header_fill = _measure_header_fill(rect, label_x, theme)
            label_bbox = _draw_measure_header_label(
                draw,
                barline_x=barline_x,
                label_x=label_x,
                header_y=y0,
                header_h=header_h,
                header_cy=header_cy,
                text=label,
                font=measure_font,
                theme=theme,
                header_fill=header_fill,
            )

            if (
                show_bpm_labels
                and measure.bpm is not None
                and _measure_shows_bpm(measure, prev_bpm)
            ):
                draw.text(
                    (label_bbox[2] + 4, header_cy),
                    _format_bpm(measure.bpm),
                    fill=theme.bpm_label,
                    font=bpm_font,
                    anchor="lm",
                )
            if measure.bpm is not None:
                prev_bpm = measure.bpm
