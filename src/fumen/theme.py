"""Visual constants for fumen rendering."""

from dataclasses import dataclass, replace

# Default canvas: 816px wide, 24px side gutters, 4 measures → 192px each.
DEFAULT_PAGE_WIDTH = 816
TRACK_BLEED = 24
DEFAULT_MEASURES_PER_ROW = 4
DEFAULT_MEASURE_WIDTH = (DEFAULT_PAGE_WIDTH - TRACK_BLEED * 2) // DEFAULT_MEASURES_PER_ROW  # 192

_PROBE_UP = DEFAULT_PAGE_WIDTH / 573


def _layout_px(probed_at_573: float) -> int:
    return max(1, round(probed_at_573 * _PROBE_UP))


_LANE_INTERIOR = _layout_px(16)
_LANE_BORDER = 2
_LANE_ACCENT = 1
_PAGE_PADDING = 16

GOGO_PINK = (255, 186, 188)
PAGE_GREY = (204, 204, 204)
LANE_GREY = (154, 153, 151)
BPM_BLUE = (0, 0, 255)


@dataclass(frozen=True)
class Theme:
    # Page + measure labels
    page_bg: tuple[int, int, int] = PAGE_GREY
    measure_number: tuple[int, int, int] = (0, 0, 0)
    bpm_label: tuple[int, int, int] = BPM_BLUE
    hs_label: tuple[int, int, int] = (220, 40, 40)

    row_header_gogo: tuple[int, int, int] = GOGO_PINK
    row_header: tuple[int, int, int] = PAGE_GREY

    # Lane
    lane_bg: tuple[int, int, int] = LANE_GREY
    lane_gogo: tuple[int, int, int] = GOGO_PINK
    lane_border: tuple[int, int, int] = (0, 0, 0)
    lane_border_width: int = _LANE_BORDER
    lane_border_accent: tuple[int, int, int] = (255, 255, 255)
    lane_border_accent_width: int = _LANE_ACCENT
    grid_line: tuple[int, int, int] = (141, 141, 141)
    lane_line: tuple[int, int, int] = (210, 210, 210)
    measure_divider: tuple[int, int, int] = (255, 255, 255)

    # Notes
    don: tuple[int, int, int] = (252, 52, 52)
    ka: tuple[int, int, int] = (96, 186, 236)
    note_outline_outer: tuple[int, int, int] = (0, 0, 0)
    note_outline: tuple[int, int, int] = (255, 255, 255)
    note_outline_outer_width: int = 1
    note_outline_inner_width: int = 2
    roll: tuple[int, int, int] = (252, 186, 73)
    balloon: tuple[int, int, int] = (252, 186, 73)
    balloon_bar: tuple[int, int, int] = (252, 186, 73)
    balloon_text: tuple[int, int, int] = (0, 0, 0)
    note_outline_width: int = 2

    # Layout
    page_width: int = DEFAULT_PAGE_WIDTH
    page_padding_x: int = 0
    page_padding_top: int = _PAGE_PADDING
    page_padding_bottom: int = _PAGE_PADDING
    row_gap: int = _layout_px(10)
    row_header_height: int = _layout_px(11)
    measure_divider_width: int = 1
    measure_number_pad_x: int = 6
    hs_label_offset_x: int = 22
    measure_width: int = DEFAULT_MEASURE_WIDTH
    lane_height: int = _LANE_INTERIOR + 2 * _LANE_BORDER + 2 * _LANE_ACCENT
    track_bleed_x: int = TRACK_BLEED
    note_diameter: int = _layout_px(11)
    big_note_diameter: int = _layout_px(16)
    balloon_bar_height: int = _layout_px(6)
    font_size_measure: int = 11
    font_size_bpm: int = 10
    font_size_meta: int = 9
    measures_per_row: int = DEFAULT_MEASURES_PER_ROW
    max_grid_slots: int = 96


DEFAULT_THEME = Theme()


def _scaled_lane_height(
    theme: Theme, scale: float, lane_bw: int, lane_aw: int
) -> int:
    interior = max(12, round(_LANE_INTERIOR * scale))
    return interior + 2 * lane_bw + 2 * lane_aw


def scale_theme(theme: Theme, target_width: int) -> Theme:
    """Scale layout dimensions; target_width is total output width including track bleed."""
    scale = target_width / theme.page_width
    bleed = max(TRACK_BLEED, round(theme.track_bleed_x * scale))
    inner = target_width - theme.page_padding_x * 2 - bleed * 2
    measure_width = inner // theme.measures_per_row
    if (
        scale == 1.0
        and measure_width == theme.measure_width
        and bleed == theme.track_bleed_x
        and target_width == theme.page_width
    ):
        return theme

    lane_bw = max(1, round(theme.lane_border_width * scale))
    lane_aw = max(1, round(theme.lane_border_accent_width * scale))
    ow = max(1, round(theme.note_outline_outer_width * scale))
    iw = max(1, round(theme.note_outline_inner_width * scale))

    return replace(
        theme,
        lane_border_width=lane_bw,
        lane_border_accent_width=lane_aw,
        note_outline_outer_width=ow,
        note_outline_inner_width=iw,
        page_width=target_width,
        page_padding_top=max(0, round(theme.page_padding_top * scale)),
        page_padding_bottom=max(0, round(theme.page_padding_bottom * scale)),
        row_gap=max(2, round(theme.row_gap * scale)),
        row_header_height=max(9, round(theme.row_header_height * scale)),
        measure_divider_width=max(1, round(theme.measure_divider_width * scale)),
        measure_number_pad_x=max(4, round(theme.measure_number_pad_x * scale)),
        hs_label_offset_x=max(12, round(theme.hs_label_offset_x * scale)),
        measure_width=measure_width,
        lane_height=_scaled_lane_height(theme, scale, lane_bw, lane_aw),
        track_bleed_x=bleed,
        note_diameter=max(8, round(theme.note_diameter * scale)),
        big_note_diameter=max(14, round(theme.big_note_diameter * scale)),
        balloon_bar_height=max(4, round(theme.balloon_bar_height * scale)),
        note_outline_width=max(1, round(theme.note_outline_width * scale)),
        font_size_measure=max(7, round(theme.font_size_measure * scale)),
        font_size_bpm=max(7, round(theme.font_size_bpm * scale)),
        font_size_meta=max(6, round(theme.font_size_meta * scale)),
    )
