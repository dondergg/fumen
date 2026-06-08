# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-06-09

### Added

- README: supported TJA features (metadata, notes, commands, branching, encodings)

### Changed

- First stable release

## [0.1.0] - 2026-06-07

### Added

- TJA parser: metadata, notes, spans, branching, Shift-JIS / UTF-8
- Fumen PNG renderer: lanes, notes, rolls, balloons, gogo headers, BPM labels
- CLI: `fumen render chart.tja -o out.png`
- Python API: `parse_tja`, `render_fumen`
- Test suite with fixture charts and golden pixel probes
- Example image generator script
