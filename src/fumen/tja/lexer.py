"""Normalize TJA source lines."""

from __future__ import annotations

import re


def strip_comment(line: str) -> str:
    if "//" in line:
        return line.split("//", 1)[0]
    return line


def normalize_lines(text: str) -> list[tuple[int, str]]:
    """Return (1-based line number, stripped line) pairs."""
    result: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = strip_comment(raw).strip()
        if line:
            result.append((lineno, line))
    return result


HEADER_RE = re.compile(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$")
COMMAND_RE = re.compile(r"^#([A-Za-z0-9_]+)(?:\s+(.*))?$")
# Inline chart commands sit between note digits; names are letters only.
INLINE_COMMAND_RE = re.compile(r"^#([A-Za-z_]+)(?:\s+([^,\s#]+))?(?=[0-9,\s#]|$)")
