"""VCD (Value Change Dump) file parser with streaming support."""


def _build_full_name(scope_stack, name):
    """Build full hierarchical signal name from scope stack."""
    prefix = ".".join(s for s in scope_stack if s)
    return f"{prefix}.{name}" if prefix else name


def _parse_timescale_value(ts):
    """Convert a VCD timescale string (e.g. '1ps', '10ns') to (unit, ps_per_unit).

    Returns (unit_str, ps_per_unit).
    """
    ts = ts.lower().strip()
    import re
    m = re.match(r"(\d+)\s*(ps|ns|us|ms|s)", ts)
    if not m:
        return "ps", 1  # default
    num = int(m.group(1))
    unit = m.group(2)
    scale = {"ps": 1, "ns": 1000, "us": 1000000, "ms": 1000000000, "s": 1000000000000}
    return f"{num}{unit}", num * scale[unit]


def parse_vcd(filepath):
    """Parse a VCD file and return (signals_dict, max_time, timescale_info).

    signals_dict: {code: {'name': str, 'width': int, 'values': [(time, val), ...]}}
        'name' is the full hierarchical name (e.g. 'top.uut.clk').
        'values' are sorted by time on first access (lazy sorting).
    max_time: int, the largest timestamp in the file (in raw VCD ticks).
    timescale_info: {'unit': str, 'ps_per_unit': int, 'raw': str}
        e.g. {'unit': '1ps', 'ps_per_unit': 1, 'raw': '1ps'}
    """
    signals = {}
    scope_stack = [""]
    current_time = 0
    max_time = 0
    timescale_raw = "1ps"
    line_count = 0
    warn_unknown = set()

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_count += 1
            stripped = line.strip()
            if not stripped:
                continue

            # ── Header directives ──
            if stripped.startswith("$timescale"):
                parts = stripped.split()
                if len(parts) >= 2:
                    timescale_raw = parts[1]

            elif stripped.startswith("$scope"):
                parts = stripped.split()
                if len(parts) >= 3:
                    scope_stack.append(parts[2])

            elif stripped.startswith("$upscope"):
                if len(scope_stack) > 1:
                    scope_stack.pop()
                elif line_count < 50:
                    # Warnings only within first 50 lines (header area)
                    warn_unknown.add("$upscope underflow (too many $upscope)")

            elif stripped.startswith("$var"):
                # $var type size code name [$end|optional_suffix]
                parts = stripped.split()
                if len(parts) < 5:
                    continue
                try:
                    width = int(parts[2])
                except ValueError:
                    continue
                code = parts[3]
                name = parts[4]
                full_name = _build_full_name(scope_stack, name)
                signals[code] = {"name": full_name, "width": width, "values": []}

            elif stripped.startswith("$enddefinitions"):
                pass  # marker only

            elif stripped.startswith("$date"):
                pass  # informational

            elif stripped.startswith("$version"):
                pass  # informational

            elif stripped.startswith("$comment"):
                pass  # informational

            elif stripped.startswith("$dumpall"):
                pass  # not implemented (uncommon)

            elif stripped.startswith("$dumpon"):
                pass  # filtering not implemented

            elif stripped.startswith("$dumpoff"):
                pass  # filtering not implemented

            # ── $dumpvars / $end ──
            elif stripped.startswith("$dumpvars"):
                # Initial state values follow on subsequent lines at time 0.
                # Handled naturally by the #timestamp / scalar / vector branches.
                pass

            elif stripped == "$end":
                # Terminates $dumpvars or other blocks; no action needed.
                pass

            # ── Timestamp ──
            elif stripped.startswith("#"):
                ts_str = stripped[1:]
                # Handle hex/oct timestamps defensively
                try:
                    current_time = int(ts_str)
                except ValueError:
                    try:
                        current_time = int(ts_str, 16)
                    except ValueError:
                        warn_unknown.add(f"malformed timestamp at line {line_count}")
                        continue
                if current_time > max_time:
                    max_time = current_time

            # ── Vector value change (binary) ──
            elif stripped.startswith("b"):
                # b<binary_value> <code>
                parts = stripped.split()
                if len(parts) >= 2:
                    val = parts[0][1:]  # strip leading 'b'
                    code = parts[1]
                    sig = signals.get(code)
                    if sig is not None:
                        sig["values"].append((current_time, val))
                    elif code not in warn_unknown and line_count > 50:
                        warn_unknown.add(f"unknown signal code: {code!r}")

            # ── Scalar value change (0, 1, x, z) ──
            elif len(stripped) >= 2 and stripped[0] in "01xzXZ":
                val = stripped[0]
                code = stripped[1:]
                sig = signals.get(code)
                if sig is not None:
                    sig["values"].append((current_time, val))
                elif code not in warn_unknown and line_count > 50:
                    warn_unknown.add(f"unknown signal code: {code!r}")

            # ── Real value change ──
            elif stripped.startswith("r"):
                # r<real_value> <code> — skip for now, VCD spec allows this
                pass

            # ── Anything else ──
            else:
                if len(stripped) > 0 and line_count > 50:
                    warn_unknown.add(f"unrecognized line at {line_count}: {stripped[:60]}")

    # Compute timescale info
    unit_str, ps_per_unit = _parse_timescale_value(timescale_raw)
    timescale_info = {
        "unit": unit_str,
        "ps_per_unit": ps_per_unit,
        "raw": timescale_raw,
    }

    # Surface warnings via a small attribute
    if warn_unknown:
        signals["__warnings__"] = sorted(warn_unknown)

    return signals, max_time, timescale_info
