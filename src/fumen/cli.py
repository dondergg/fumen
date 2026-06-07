"""CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fumen.model import BranchPath
from fumen.tja.parser import ParseError, parse_tja
from fumen.render.renderer import render_fumen


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fumen",
        description="Render fumen PNG from a TJA chart",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    render_p = sub.add_parser("render", help="Render a TJA file to PNG")
    render_p.add_argument("tja", type=Path, help="Path to .tja file")
    render_p.add_argument("-o", "--output", type=Path, required=True, help="Output PNG path")
    render_p.add_argument(
        "--course",
        default="0",
        help="Course index or name (0-4, Easy, かんたん, …)",
    )
    render_p.add_argument(
        "--branch",
        default="normal",
        choices=["normal", "advanced", "master"],
        help="Branch path when chart uses branching",
    )
    render_p.add_argument("--width", type=int, default=None, help="Output image width in px")
    render_p.add_argument("--font-path", type=str, default=None, help="TTF/OTF for CJK titles")

    args = parser.parse_args(argv)

    if args.command == "render":
        try:
            branch = BranchPath(args.branch)
            course_sel: str | int = args.course
            if str(args.course).isdigit():
                course_sel = int(args.course)
            song, course = parse_tja(args.tja, course=course_sel, branch=branch)
            render_fumen(
                song,
                course,
                args.output,
                width=args.width,
                font_path=args.font_path,
            )
            print(f"Wrote {args.output}")
            return 0
        except ParseError as e:
            print(f"Parse error: {e}", file=sys.stderr)
            if "Course not found" in str(e):
                return 2
            return 1
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
