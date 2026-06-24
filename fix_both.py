"""Fix: change const to let, add radix features to renderer."""
import re

with open('C:\\Users\\d1985\\Desktop\\vcd2wave\\vcd2wave\\renderer.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Already done: const -> let
# Add radix button to toolbar
# Find the "Open" button and add radix button after it
old = '<button id="openBtn" onclick="openVCD()">&#128194; Open</button>'
new = '<button id="openBtn" onclick="openVCD()">&#128194; Open</button>\n  <button id="radixBtn" onclick="cycleRadix()" class="primary">BIN</button>'
c = c.replace(old, new)

# Replace bus value display in loop (raw version)
old_bus1 = r"if (x2-x1>20) html += '<text x=\"' + (x1+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + prevV + '</text>';"
new_bus1 = r"if (x2-x1>20) { var rv = sig.raw && sig.raw[j] ? sig.raw[j][1] : prevV; html += '<text x=\"' + (x1+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + fmtBus(rv) + '</text>'; }"

# Replace end-of-signal bus value
old_bus2 = r"if (xEnd-prevT*px-LABEL_W>20) html += '<text x=\"' + (prevT*px+LABEL_W+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + prevV + '</text>';"
new_bus2 = r"if (xEnd-prevT*px-LABEL_W>20) { var lr = sig.raw && sig.raw[sig.raw.length-1] ? sig.raw[sig.raw.length-1][1] : prevV; html += '<text x=\"' + (prevT*px+LABEL_W+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + fmtBus(lr) + '</text>'; }"

c = c.replace(old_bus1, new_bus1)
c = c.replace(old_bus2, new_bus2)

# Also need to add the same changes for the compare section (second call to drawSignals)
# The drawSignals function handles both, so it should be OK.

with open('C:\\Users\\d1985\\Desktop\\vcd2wave\\vcd2wave\\renderer.py', 'w', encoding='utf-8') as f:
    f.write(c)

# Verify
count_raw = c.count('sig.raw &&')
print(f"sig.raw references: {count_raw}")
print("Done!")
