# Fumen

[![license](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![tests](https://github.com/dondergg/fumen/actions/workflows/test.yml/badge.svg)](https://github.com/dondergg/fumen/actions/workflows/test.yml)

Render fumen PNGs from `.tja` charts.

```bash
pip install git+https://github.com/dondergg/fumen.git
fumen render chart.tja -o chart.png
```

## Supported TJA features

### Metadata

`TITLE`, `SUBTITLE`, `BPM`, `COURSE`, `LEVEL`, `BALLOON`, and branch-specific balloon lists (`BALLOONNOR`, `BALLOONEXP`, `BALLOONMAS`).

### Notes

| Char | Meaning |
|------|---------|
| `0` | Rest |
| `1` / `A` | Don |
| `2` / `B` | Ka |
| `3` | Big don |
| `4` | Big ka |
| `5`–`8` | Roll (head/tail) |
| `6` | Big roll |
| `7` | Balloon |
| `9` | Big balloon |
| `F` | Hidden (skipped) |

### Commands

| Command | Rendered |
|---------|----------|
| `#GOGOSTART` / `#GOGOEND` | Salmon gogo header + lane tint (partial spans supported) |
| `#BPMCHANGE` | BPM label in measure header |
| `#HSPEED` | Red `HS …` label in measure header |
| `#BARLINEOFF` / `#BARLINEON` | Hide/show white measure divider |
| `#MEASURE`, `#DELAY` | Parsed (timing only, not drawn) |
| `#LYRIC` | Parsed, not drawn |
| `#SCROLL`, `#HBSCROLL`, `#BMSCROLL` | Parsed, not drawn (gameplay scroll) |

### Branching

`#BRANCHSTART` / `#BRANCHEND`, `#N` / `#E` / `#R`, `#NORMAL` / `#ADVANCED` / `#MASTER`, `#SECTION`, `#LEVELHOLD` / `#LEVELHOLDEND`. Select a path with `--branch normal|advanced|master`.

### Encodings

UTF-8 (with or without BOM), Shift-JIS / CP932.

## Links

- [CONTRIBUTING.md](CONTRIBUTING.md) — setup, CLI, API
- [CHANGELOG.md](CHANGELOG.md)
- [LICENSE](LICENSE) — GPLv3

## Examples

| | |
|:---:|:---:|
| `barline_off.tja` | `bpm_170.tja` |
| ![barline_off](.github/examples/barline_off.png) | ![bpm_170](.github/examples/bpm_170.png) |
| `bpm_200.tja` | `bpm_row.tja` |
| ![bpm_200](.github/examples/bpm_200.png) | ![bpm_row](.github/examples/bpm_row.png) |
| `branch.tja` | `cross_measure.tja` |
| ![branch](.github/examples/branch.png) | ![cross_measure](.github/examples/cross_measure.png) |
| `cross_row_roll.tja` | `dense_patterns.tja` |
| ![cross_row_roll](.github/examples/cross_row_roll.png) | ![dense_patterns](.github/examples/dense_patterns.png) |
| `multi_course.tja` (course 0) | `multi_course.tja` (course 3) |
| ![multi_course_course0](.github/examples/multi_course_course0.png) | ![multi_course_course3](.github/examples/multi_course_course3.png) |
| `partial_gogo.tja` | `showcase.tja` |
| ![partial_gogo](.github/examples/partial_gogo.png) | ![showcase](.github/examples/showcase.png) |
| `simple.tja` | |
| ![simple](.github/examples/simple.png) | |
