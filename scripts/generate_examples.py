#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from fumen.render.renderer import render_fumen
from fumen.tja.parser import parse_tja

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
EXAMPLES = ROOT / "examples"
WIDTH = 816


def _output_name(tja_name: str, course_id: int, multi: bool) -> str:
    stem = Path(tja_name).stem
    if multi:
        return f"{stem}_course{course_id}.png"
    return f"{stem}.png"


def _discover_jobs() -> list[tuple[Path, int, str]]:
    jobs: list[tuple[Path, int, str]] = []
    for path in sorted(FIXTURES.glob("*.tja")):
        song, _ = parse_tja(path, course=0)
        multi = len(song.courses) > 1
        for course in song.courses:
            out_name = _output_name(path.name, course.course_id, multi)
            jobs.append((path, course.course_id, out_name))
    return jobs


def main() -> None:
    EXAMPLES.mkdir(exist_ok=True)
    for path, course_id, out_name in _discover_jobs():
        song, chart = parse_tja(path, course=course_id)
        out = EXAMPLES / out_name
        render_fumen(song, chart, out, width=WIDTH)
        print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
