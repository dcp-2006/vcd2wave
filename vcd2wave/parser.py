"""VCD (Value Change Dump) file parser."""


def parse_vcd(filepath):
    """Parse a VCD file and return (signals_dict, max_time).

    signals_dict: {code: {'name': str, 'width': int, 'values': [(time, val), ...]}}
    """

    signals = {}
    scope_stack = [""]
    current_time = 0
    max_time = 0

    with open(filepath, "r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("$scope"):
            parts = line.split()
            if len(parts) >= 3:
                scope_stack.append(parts[2])

        elif line.startswith("$upscope"):
            if scope_stack:
                scope_stack.pop()

        elif line.startswith("$var"):
            # $var type size code name $end
            parts = line.split()
            if len(parts) >= 5:
                width = int(parts[2])
                code = parts[3]
                name = parts[4]
                full_name = name
                if scope_stack and scope_stack[-1]:
                    full_name = f"{scope_stack[-1]}.{name}"
                signals[code] = {"name": full_name, "width": width, "values": []}

        elif line.startswith("#") and line[1:].isdigit():
            current_time = int(line[1:])
            max_time = max(max_time, current_time)

        elif line.startswith("b"):
            parts = line.split()
            if len(parts) >= 2:
                val = parts[0][1:]
                code = parts[1]
                if code in signals:
                    signals[code]["values"].append((current_time, val))

        elif len(line) >= 2 and line[0] in "01xzXZ":
            val = line[0]
            code = line[1:]
            if code in signals:
                signals[code]["values"].append((current_time, val))

        elif line.startswith("$dumpvars"):
            while i + 1 < len(lines):
                i += 1
                dl = lines[i].strip()
                if dl == "$end":
                    break
                if dl.startswith("b"):
                    parts = dl.split()
                    if len(parts) >= 2 and parts[1] in signals:
                        signals[parts[1]]["values"].append((0, parts[0][1:]))
                elif len(dl) >= 2 and dl[0] in "01xzXZ" and dl[1:] in signals:
                    signals[dl[1:]]["values"].append((0, dl[0]))

        i += 1

    return signals, max_time
