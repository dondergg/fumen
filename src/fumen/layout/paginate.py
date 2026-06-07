"""Split measures into rows."""

from __future__ import annotations

from fumen.model import Measure


def paginate_measures(
    measures: list[Measure],
    per_row: int = 4,
) -> list[list[Measure]]:
    rows: list[list[Measure]] = []
    for i in range(0, len(measures), per_row):
        rows.append(measures[i : i + per_row])
    return rows
