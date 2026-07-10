# vcd2wave

**VCD (Value Change Dump) to HTML waveform visualizer.**

A lightweight, zero-dependency Python tool that converts VCD files from EDA tools (ModelSim, Vivado, iverilog, etc.) into interactive HTML waveform views. No more firing up heavy EDA software just to glance at a waveform.

[![Python Tests](https://github.com/dcp-2006/vcd2wave/actions/workflows/python-test.yml/badge.svg?branch=master)](https://github.com/dcp-2006/vcd2wave/actions/workflows/python-test.yml)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)

---

## Features

- **Zero dependencies** — pure Python 3 standard library only
- **Interactive viewer** — zoom in/out, drag to scroll, resizable, dark/light themes
- **Multi-signal support** — single-bit, multi-bit buses, hierarchical scopes
- **Smart time axis** — auto-scales between ps/ns/us/ms; respects VCD `$timescale`
- **Measurement cursors** — place up to 2 cursors, drag to measure, Δt display
- **Compare mode** — load a second VCD file and overlay it for side-by-side diff
- **Annotations** — add labels at specific timestamps
- **Export** — PNG and SVG export of the waveform view
- **Bus radix** — toggle between BIN/OCT/DEC/HEX display
- **CLI** — full `argparse` CLI with `--help`, `--output`, `--no-open`, `--timescale`, `--title`
- **Portable** — single-file CLI (`pip install .`) or `python -m vcd2wave`
- **EDA tool agnostic** — works with ModelSim, Vivado, iverilog, and any tool outputting standard VCD

## Quick Start

\`\`\`bash
# One-shot conversion
python -m vcd2wave dump.vcd

# Specify output path
python -m vcd2wave dump.vcd -o output.html

# Full CLI options
python -m vcd2wave --help
python -m vcd2wave dump.vcd --no-open --timescale 1ns --title "My Wave"
\`\`\`

The generated HTML opens automatically in your browser (use `--no-open` to disable).

## Examples

```bash
# Using iverilog
iverilog -o sim.vvp test.v tb.v
vvp sim.vvp
python -m vcd2wave dump.vcd

# Using ModelSim (via DO script)
# vsim -c top -do "log -r /*; run 1us; vcd file out.vcd; vcd add -r /*; quit"
python -m vcd2wave out.vcd
```

## Output Preview

The generated HTML features:
- A sticky toolbar with zoom controls (+/−, slider, reset), theme toggle (dark/light)
- Horizontal scroll and mouse-drag panning
- Color-coded signal rows (single-bit vs. bus)
- Measurement cursors — click to place, drag to measure, Δt displayed automatically
- Bus radix toggle (BIN/OCT/DEC/HEX)
- Compare mode — load a second VCD and overlay signals
- Export to PNG or SVG
- Auto-scaled grid lines with time labels (respects `$timescale`)
- Responsive layout, works in any modern browser
- Welcome screen with drag-and-drop file loading

## Project Structure

```
vcd2wave/
├── vcd2wave/              # Core package
│   ├── __init__.py
│   ├── parser.py          # VCD file parser
│   └── renderer.py        # HTML/SVG renderer
├── tests/                 # Unit tests
├── examples/              # Example VCD files and testbenches
│   ├── test_counter.v
│   ├── test_fsm.v
│   ├── counter.vcd
│   └── fsm.vcd
├── .github/workflows/     # CI config
├── README.md
├── LICENSE
├── setup.py
└── .gitignore
```

## Technical Details

The parser handles:
- `$var` declarations for both scalar and vector signals
- Nested `$scope` / `$upscope` hierarchies (full hierarchical names preserved)
- Scalar value changes (`0`, `1`, `x`, `z`)
- Vector value changes (`b` binary format)
- Timestamp events (`#` format)
- `$timescale` directives (used for accurate time axis labels)
- Streaming line-by-line parsing (safe for large VCD files)
- Graceful handling of `$dumpall`, `$dumpon`, `$dumpoff`, `r` real values

The renderer generates pure SVG/HTML — no JavaScript libraries required.

## Installation

```bash
# From source
git clone https://github.com/dcp-2006/vcd2wave.git
cd vcd2wave
pip install .
vcd2wave input.vcd

# Or run directly without install
python -m vcd2wave input.vcd

# Or grab just the CLI script
curl -O https://raw.githubusercontent.com/dcp-2006/vcd2wave/master/vcd2wave.py
python vcd2wave.py input.vcd
```

## Tests

```bash
python -m pytest tests/
```

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

Issues and pull requests are welcome. For feature requests, please open an issue first.
