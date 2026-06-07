# Contributing

## Setup

```bash
git clone https://github.com/dondergg/fumen.git
cd fumen
pip install -e ".[dev]"
```

## Tests

```bash
pytest
```

CI runs on Python 3.10–3.13 (see `.github/workflows/test.yml`).

### Regenerate fixtures

```bash
python scripts/generate_examples.py   # local previews in examples/ (gitignored)
python scripts/record_golden_probes.py   # updates tests/fixtures/golden_probes.json
```

## Usage

```bash
fumen render path/to/chart.tja -o fumen.png --course Easy --branch normal
```

Or:

```bash
python -m fumen render path/to/chart.tja -o fumen.png
```

### CLI options

| Flag | Description |
|------|-------------|
| `-o`, `--output` | Output PNG path (required) |
| `--course` | Course index (`0`–`4`) or name (`Easy`, `かんたん`, …) |
| `--branch` | Branch path: `normal`, `advanced`, or `master` (default: `normal`) |
| `--width` | Total image width in pixels (default: **816**) |
| `--font-path` | Path to a TTF/OTF with CJK support (optional) |

Exit codes: `0` success, `1` parse error, `2` course not found.

### Python API

```python
from fumen import parse_tja, render_fumen

song, course = parse_tja("chart.tja", course=0)
render_fumen(song, course, "out.png", width=816)
```

## Canvas layout

- **816px** wide, **24px** side bleed, **192px** measures (4 per row)
- **16px** gray margin above and below the chart

Pass `--width 1280` (or any width) to scale layout proportionally.

## Supported TJA features

- Metadata: `TITLE`, `SUBTITLE`, `BPM`, `COURSE`, `LEVEL`, `BALLOON`, branch-specific `BALLOON*`
- Notes: `0`–`9`, `A`/`B` (multiplayer as don/ka), `F` (hidden, skipped)
- Commands: `#GOGOSTART`/`#GOGOEND`, `#BPMCHANGE`, `#MEASURE`, `#DELAY`, `#BARLINEOFF`/`#BARLINEON`, `#LYRIC` (parsed, not drawn)
- Branching: `#BRANCHSTART`, `#N`/`#E`/`#R`, `#NORMAL`/`#ADVANCED`/`#MASTER`, `#SECTION`, `#LEVELHOLD`, etc.
- Encodings: UTF-8 (with/without BOM), Shift-JIS

Not drawn (gameplay scroll only): `#SCROLL`, `#HBSCROLL`, `#BMSCROLL`.

`#HSPEED` → red `HS …` label in the measure header.

`#BARLINEOFF` hides the white measure divider after that measure.

## Project layout

```
src/fumen/
  tja/       parser, lexer, notes, branch
  layout/    geometry, pagination
  render/    lanes, notes, renderer
  cli.py
tests/fixtures/   sample .tja charts
scripts/          example + golden probe generators
```

## License

By contributing, you agree that your contributions are licensed under the same terms as the project: **GNU GPLv3**. See [LICENSE](LICENSE).
