"""Measure number placement in pink header bands."""

from PIL import Image, ImageDraw

from fumen.render.canvas import _load_font, draw_text_left_middle
from fumen.theme import DEFAULT_THEME


def test_measure_number_sits_right_of_barline():
    img = Image.new("RGB", (100, 24), DEFAULT_THEME.row_header)
    draw = ImageDraw.Draw(img)
    font = _load_font(DEFAULT_THEME.font_size_measure, None)
    barline_x = 20
    cy = 12
    label_x = barline_x + DEFAULT_THEME.measure_divider_width + DEFAULT_THEME.measure_number_pad_x
    bbox = draw_text_left_middle(draw, label_x, cy, "52", font, (0, 0, 0))
    assert bbox[0] >= barline_x + DEFAULT_THEME.measure_divider_width
