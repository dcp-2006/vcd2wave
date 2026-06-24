# vcd2wave

**VCD (Value Change Dump) to HTML waveform visualizer.**

A lightweight, zero-dependency Python tool that converts VCD files from EDA tools (ModelSim, Vivado, iverilog, etc.) into interactive HTML waveform views. No more firing up heavy EDA software just to glance at a waveform.

[![Python Tests](https://github.com/dcp-2006/vcd2wave/actions/workflows/python-test.yml/badge.svg)](https://github.com/dcp-2006/vcd2wave/actions/workflows/python-test.yml)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Features

- **Zero dependencies** — pure Python 3 standard library only
- **Interactive viewer** — zoom in/out, drag to scroll, resizable
- **Multi-signal support** — single-bit, multi-bit buses, hierarchical scopes
- **Smart time axis** — auto-scales between ps/ns/us/ms
- **Portable** — single-file CLI, or install as a package
- **EDA tool agnostic** — works with any tool that outputs standard VCD

## Quick Start

```bash
# One-shot conversion
python vcd2wave.py dump.vcd

# Specify output path
python vcd2wave.py dump.vcd output.html

# Install system-wide
pip install .
vcd2wave dump.vcd
```

The generated HTML opens automatically in your browser.

## Examples

```bash
# Using iverilog
iverilog -o sim.vvp test.v tb.v
vvp sim.vvp
vcd2wave dump.vcd

# Using ModelSim (via DO script)
# vsim -c top -do "log -r /*; run 1us; vcd file out.vcd; vcd add -r /*; quit"
vcd2wave out.vcd
```

## Output Preview

The generated HTML features:
- A sticky toolbar with zoom controls (+/−, slider, reset)
- Horizontal scroll and mouse-drag panning
- Color-coded signal rows (single-bit vs. bus)
- Auto-scaled grid lines with time labels
- Responsive layout, works in any modern browser

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
- Nested `$scope` / `$upscope` hierarchies
- Scalar value changes (`0`, `1`, `x`, `z`)
- Vector value changes (`b` binary format)
- Timestamp events (`#` format)

The renderer generates pure SVG/HTML — no JavaScript libraries required.

## Installation

```bash
# From source
git clone https://github.com/dcp-2006/vcd2wave.git
cd vcd2wave
pip install .

# Or just grab the CLI script
curl -O https://raw.githubusercontent.com/dcp-2006/vcd2wave/main/vcd2wave.py
```

## Tests

```bash
python -m pytest tests/
```

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

Issues and pull requests are welcome. For feature requests, please open an issue first.
