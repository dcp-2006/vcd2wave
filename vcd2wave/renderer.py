"""HTML waveform renderer."""


def gen_html(signals, max_time, title="Waveform"):
    """Generate an HTML page visualizing the parsed VCD signals."""

    svg_width = 900
    margin_left = 200
    wave_area = svg_width - margin_left - 20
    ns_per_px = max_time / wave_area if max_time > 0 else 1

    # Filter top-level signals
    filtered = {}
    for code, sig in signals.items():
        name = sig["name"]
        if "." not in name:
            filtered[code] = sig

    if len(filtered) < 5:
        filtered = signals

    rows = []
    row_h = 45
    total_h = len(filtered) * row_h + 60

    for idx, (code, sig) in enumerate(filtered.items()):
        y = idx * row_h + 30
        name = sig["name"]
        width = sig["width"]
        vals = sorted(sig["values"], key=lambda x: x[0])

        disp_name = name.split(".")[-1] if "." in name else name
        if width > 1:
            disp_name += f"[{width - 1}:0]"

        rows.append(f"""
        <div class="row" style="top:{y}px">
            <div class="label">{disp_name}</div>
            <div class="wave">"""
        )

        svg_parts = []
        if not vals:
            rows.append("</div></div>")
            continue

        prev_time = vals[0][0]
        prev_val = vals[0][1]

        # Grid lines
        for t in range(0, max_time + 1, max(1, max_time // 20)):
            x = int(t / ns_per_px)
            svg_parts.append(
                f'<line x1="{x}" y1="0" x2="{x}" y2="{row_h - 5}" '
                f'stroke="#ecf0f1" stroke-width="1"/>'
            )

        for t, val in vals:
            x1 = int(prev_time / ns_per_px)
            x2 = int(t / ns_per_px)

            if width == 1:
                y_val = 8 if prev_val in ("1",) else row_h - 18 if prev_val in ("0",) else row_h // 2
                svg_parts.append(
                    f'<line x1="{x1}" y1="{y_val}" x2="{x2}" y2="{y_val}" '
                    f'stroke="#2c3e50" stroke-width="2"/>'
                )
                if val != prev_val:
                    y_new = 8 if val in ("1",) else row_h - 18 if val in ("0",) else row_h // 2
                    svg_parts.append(
                        f'<line x1="{x2}" y1="{y_val}" x2="{x2}" y2="{y_new}" '
                        f'stroke="#2c3e50" stroke-width="2"/>'
                    )
            else:
                y_bus = row_h - 20
                mid = (x1 + x2) / 2
                svg_parts.append(
                    f'<line x1="{x1}" y1="{y_bus}" x2="{x2}" y2="{y_bus}" '
                    f'stroke="#2980b9" stroke-width="1.5"/>'
                )
                svg_parts.append(
                    f'<text x="{mid}" y="{y_bus - 3}" text-anchor="middle" '
                    f'font-size="11" fill="#2980b9">{prev_val}</text>'
                )

            prev_val = val
            prev_time = t

        # Extend to end
        x_end = int(max_time / ns_per_px)
        if width == 1:
            y_end = 8 if prev_val in ("1",) else row_h - 18
            svg_parts.append(
                f'<line x1="{x_end}" y1="{y_end}" x2="{wave_area}" y2="{y_end}" '
                f'stroke="#2c3e50" stroke-width="2"/>'
            )
        else:
            y_bus = row_h - 20
            svg_parts.append(
                f'<line x1="{x_end}" y1="{y_bus}" x2="{wave_area}" y2="{y_bus}" '
                f'stroke="#2980b9" stroke-width="1.5"/>'
            )
            mid = (x_end + wave_area) / 2
            svg_parts.append(
                f'<text x="{mid}" y="{y_bus - 3}" text-anchor="middle" '
                f'font-size="11" fill="#2980b9">{prev_val}</text>'
            )

        rows.append(
            f'<svg width="{wave_area}" height="{row_h - 5}" style="display:block;">'
            + "\n".join(svg_parts)
            + "</svg></div></div>"
        )

    # Time axis
    time_y = len(filtered) * row_h + 30
    time_axis = (
        f'<div class="row" style="top:{time_y}px">'
        f'<div class="label"></div><div class="wave" style="border:none;">'
        f'<svg width="{wave_area}" height="20">'
    )
    for t in range(0, max_time + 1, max(1, max_time // 10)):
        x = int(t / ns_per_px)
        unit = "ps"
        disp_t = t
        if t >= 1000:
            disp_t = t / 1000
            unit = "ns"
        if t >= 1000000:
            disp_t = t / 1000000
            unit = "us"
        if t >= 1000000000:
            disp_t = t / 1000000000
            unit = "ms"
        time_axis += (
            f'<text x="{x}" y="15" text-anchor="middle" '
            f'font-size="9" fill="#7f8c8d">'
            f'{disp_t:.0f}{unit}</text>'
        )
    time_axis += "</svg></div></div>"

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{title}</title>
<style>
* {{margin:0;padding:0}}
body {{font-family:Consolas,'Courier New',monospace;background:#fff;padding:10px}}
.header {{margin:10px 0 20px 200px;color:#2c3e50}}
.header h2 {{font-size:18px;margin-bottom:4px}}
.header p {{font-size:12px;color:#7f8c8d}}
.wave-box {{position:relative;margin:10px 0;
    border-top:1px solid #bdc3c7;overflow:hidden}}
.row {{position:absolute;left:0;right:0;height:{row_h}px;display:flex;align-items:center}}
.label {{position:absolute;left:0;width:190px;font-size:12px;color:#2c3e50;
    font-weight:bold;padding:0 10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.wave {{position:absolute;left:200px;right:10px;height:{row_h - 5}px;
    border-bottom:1px solid #ecf0f1;overflow:hidden}}
.footer {{text-align:center;margin-top:20px;font-size:11px;color:#95a5a6}}
</style></head><body>
<div class="header">
    <h2>{title}</h2>
    <p>{len(filtered)} signals | {max_time} ps | vcd2wave</p>
</div>
<div class="wave-box" style="height:{len(filtered) * row_h + 60}px">
{"".join(rows)}
{time_axis}
</div>
<p class="footer">Generated by vcd2wave &mdash; {title}</p>
</body></html>"""

    return html
