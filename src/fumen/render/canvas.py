"""Font loading and canvas creation."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from fumen.layout.geometry import Layout
from fumen.theme import Theme


def draw_text_left_middle(
    draw: ImageDraw.ImageDraw,
    x: float,
    cy: float,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    """Draw text with its left edge at x and vertical center at cy."""
    bbox = draw.textbbox((0, 0), text, font=font)
    y = int(cy - (bbox[1] + bbox[3]) / 2)
    draw.text((int(x), y), text, font=font, fill=fill)
    return draw.textbbox((int(x), y), text, font=font)


def draw_text_centered(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> tuple[int, int, int, int]:
    """Draw text with its bounding-box center at (cx, cy). Works with any PIL font."""
    bbox = draw.textbbox((0, 0), text, font=font)
    # int(+0.5): avoid Python round-half-to-even leaving balloon digits 1px left
    x = int(cx - (bbox[0] + bbox[2]) / 2 + 0.5)
    y = int(cy - (bbox[1] + bbox[3]) / 2 + 0.5)
    draw.text((x, y), text, font=font, fill=fill)
    return draw.textbbox((x, y), text, font=font)


def _load_font(size: int, font_path: str | None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path and Path(font_path).exists():
        return ImageFont.truetype(font_path, size)
    for name in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "Arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_canvas(layout: Layout, theme: Theme) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (layout.page_width, layout.page_height), theme.page_bg)
    return img, ImageDraw.Draw(img)
