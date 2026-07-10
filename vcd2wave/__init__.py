"""vcd2wave - Convert VCD waveform files to interactive HTML visualizations."""

import argparse
import os
import sys

from .parser import parse_vcd
from .renderer import gen_html

__version__ = "1.1.0"


def _open_in_browser(path):
    """Open the generated HTML in the default browser."""
    import webbrowser
    # On Windows, prefer msedge over system default (may be slow browser)
    if sys.platform == "win32":
        edge_path = (
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        )
        for p in edge_path:
            if os.path.exists(p):
                webbrowser.register("msedge", None, webbrowser.BackgroundBrowser(p))
                break
    webbrowser.open(f"file://{os.path.abspath(path)}")


def build_parser():
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="vcd2wave",
        description="Convert VCD waveform files to interactive HTML visualizations.",
        epilog="Example: vcd2wave dump.vcd -o wave.html",
    )
    p.add_argument("input", metavar="INPUT", help="Path to the .vcd file")
    p.add_argument("-o", "--output", metavar="FILE",
                    help="Output HTML path (default: INPUT.html)")
    p.add_argument("--no-open", action="store_true",
                    help="Do not open the generated HTML in browser")
    p.add_argument("--no-browser", action="store_true", dest="no_open",
                    help=argparse.SUPPRESS)  # alias
    p.add_argument("--timescale", metavar="UNIT",
                    help="Override timescale (e.g. '1ns', '10ps')")
    p.add_argument("--title", metavar="TITLE",
                    help="Page title (default: input filename)")
    p.add_argument("-V", "--version", action="version",
                    version=f"vcd2wave {__version__}")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    vcd_path = args.input
    if not os.path.exists(vcd_path):
        print(f"Error: file not found: {vcd_path}", file=sys.stderr)
        sys.exit(1)

    html_path = args.output or vcd_path.rsplit(".", 1)[0] + ".html"
    title = args.title or os.path.splitext(os.path.basename(vcd_path))[0]

    print(f"[*] Parsing {vcd_path}...")
    signals, max_time, timescale_info = parse_vcd(vcd_path)

    if args.timescale:
        from .parser import _parse_timescale_value
        unit_str, ps_per_unit = _parse_timescale_value(args.timescale)
        timescale_info = {"unit": unit_str, "ps_per_unit": ps_per_unit, "raw": args.timescale}

    if "__warnings__" in signals:
        for w in signals.pop("__warnings__"):
            print(f"[!] Warning: {w}", file=sys.stderr)

    print(f"[*] {len(signals)} signals, {max_time} ticks ({timescale_info['unit']} per tick)")

    print("[*] Generating HTML...")
    html = gen_html(signals, max_time, timescale_info, title)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Output: {os.path.abspath(html_path)}")

    if not args.no_open:
        _open_in_browser(html_path)


if __name__ == "__main__":
    main()
