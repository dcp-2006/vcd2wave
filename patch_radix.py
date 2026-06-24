import re

with open('C:\\Users\\d1985\\Desktop\\vcd2wave\\vcd2wave\\renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add radix state
old = 'let annotations = [];\nlet annId = 0;\n// Cursors'
new = 'let annotations = [];\nlet annId = 0;\nlet radices = {};\nlet radixLabels = {16:"H",10:"D",8:"O",2:"B"};\n\nfunction fmtWithRadix(binStr, radix) {\n  if (radix === 2) return binStr;\n  try {\n    var dec = parseInt(binStr, 2);\n    if (radix === 8) return dec.toString(8);\n    if (radix === 10) return dec.toString(10);\n    return dec.toString(16).toUpperCase();\n  } catch(e) { return binStr; }\n}\n\nfunction getRadix(name) {\n  if (radices[name] === undefined) radices[name] = 16;\n  return radices[name];\n}\n\nfunction cycleRadix(name) {\n  var order = [16,10,8,2];\n  var r = getRadix(name);\n  for (var i=0;i<order.length;i++) { if (order[i]===r) { radices[name]=order[(i+1)%order.length]; break; } }\n  draw();\n}\n// Cursors'
content = content.replace(old, new)

# 2. Bus value display - use fmtWithRadix with raw binary
old = "if (x2-x1>20) html += '<text x=\"' + (x1+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + prevV + '</text>';"
# First occurrence (inside loop)
new_val = "if (x2-x1>20) { var rawV = sig.raw && sig.raw[j] ? sig.raw[j][1] : prevV; html += '<text x=\"' + (x1+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + fmtWithRadix(rawV, getRadix(dn)) + '</text>'; }"
content = content.replace(old, new_val)

# 3. End-of-signal bus value
old = "if (xEnd-prevT*px-LABEL_W>20) html += '<text x=\"' + (prevT*px+LABEL_W+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + prevV + '</text>';"
new_end = "if (xEnd-prevT*px-LABEL_W>20) { var lastRaw = sig.raw && sig.raw[sig.raw.length-1] ? sig.raw[sig.raw.length-1][1] : prevV; html += '<text x=\"' + (prevT*px+LABEL_W+4) + '\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"10\" font-family=\"Consolas\" fill=\"' + (suffix?'#d35400':busT) + '\">' + fmtWithRadix(lastRaw, getRadix(dn)) + '</text>'; }"
content = content.replace(old, new_end)

# 4. Add radix button next to bus signal name
old_label = "html += '<text x=\"8\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"11\" font-weight=\"600\" fill=\"' + lc + '\">' + dn + '</text>';"
new_label = "html += '<text x=\"8\" y=\"' + (y0+ROW_H/2+4) + '\" font-size=\"11\" font-weight=\"600\" fill=\"' + lc + '\">' + dn + '</text>';\n      if (isBus) {\n        var r = getRadix(dn);\n        html += '<rect x=\"' + (LABEL_W-28) + '\" y=\"' + (y0+8) + '\" width=\"24\" height=\"18\" rx=\"3\" fill=\"#3498db\" style=\"cursor:pointer\" onclick=\"cycleRadix(\\'' + dn.replace(/'/g,'') + '\\')\"/>';\n        html += '<text x=\"' + (LABEL_W-16) + '\" y=\"' + (y0+20) + '\" text-anchor=\"middle\" font-size=\"10\" font-weight=\"bold\" fill=\"#fff\" style=\"cursor:pointer\" onclick=\"cycleRadix(\\'' + dn.replace(/'/g,'') + '\\')\">' + radixLabels[r] + '</text>';\n      }"

content = content.replace(old_label, new_label)

# 5. When comparing, use raw_trans from compareData too
old_compare_trans = "var trans = sig.trans;\n      if (!trans||trans.length===0) continue;"
content = content.replace(old_compare_trans, "var trans = sig.trans;\n      if (!trans||trans.length===0) continue;\n      if (!sig.raw && sigData.length > 0 && i < sigData.length) sig.raw = sigData[i].raw;")

with open('C:\\Users\\d1985\\Desktop\\vcd2wave\\vcd2wave\\renderer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK')
