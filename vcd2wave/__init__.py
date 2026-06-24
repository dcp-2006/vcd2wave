"""vcd2wave - Convert VCD waveform files to interactive HTML visualizations."""

from .parser import parse_vcd
from .renderer import gen_html

__version__ = "1.0.0"


def main():
    import sys, os

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: python -m vcd2wave <input.vcd> [output.html]", file=sys.stderr)
        sys.exit(1)

    vcd_path = sys.argv[1]
    if not os.path.exists(vcd_path):
        print(f"Error: file not found: {vcd_path}", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[2] if len(sys.argv) > 2 else vcd_path.replace(".vcd", ".html")
    title = os.path.splitext(os.path.basename(vcd_path))[0]

    print(f"[*] Parsing {vcd_path}...")
    signals, max_time = parse_vcd(vcd_path)
    print(f"[*] {len(signals)} signals, {max_time} ps")

    print("[*] Generating HTML...")
    html = gen_html(signals, max_time, title)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Output: {html_path}")

    if sys.platform == "win32":
        # Force use Edge, not system default (which may be Quark)
        os.system(f'start msedge "{html_path}"')


if __name__ == "__main__":
    main()
