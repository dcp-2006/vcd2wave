"""HTML waveform renderer with measurement, comparison, annotations."""

import json


def _parse_vcd_for_compare(filepath):
    """Minimal VCD parser for comparison feature."""
    signals = {}
    scope_stack = [""]
    max_time = 0
    current_time = 0
    with open(filepath) as f:
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
            parts = line.split()
            if len(parts) >= 5:
                width = int(parts[2])
                code = parts[3]
                name = parts[4]
                full = f"{scope_stack[-1]}.{name}" if scope_stack[-1] else name
                signals[code] = {"name": full, "width": width, "values": []}
        elif line.startswith("#") and line[1:].isdigit():
            current_time = int(line[1:])
            max_time = max(max_time, current_time)
        elif line.startswith("b"):
            parts = line.split()
            if len(parts) >= 2 and parts[1] in signals:
                signals[parts[1]]["values"].append((current_time, parts[0][1:]))
        elif len(line) >= 2 and line[0] in "01xzXZ" and line[1:] in signals:
            signals[line[1:]]["values"].append((current_time, line[0]))
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
    sig_list = []
    for code, sig in signals.items():
        name = sig["name"].split(".")[-1]
        w = sig["width"]
        vals = sorted(sig["values"], key=lambda x: x[0])
        trans = []
        for t, v in vals:
            if w == 1:
                trans.append((t, "1" if v in ("1",) else "0"))
            else:
                try:
                    if v.replace("0", "").replace("1", "") == "":
                        trans.append((t, format(int(v, 2), "X")))
                    else:
                        trans.append((t, v))
                except:
                    trans.append((t, v))
        sig_list.append({"name": name, "width": w, "trans": trans})
    return sig_list, max_time


def gen_html(signals, max_time, title="Waveform"):
    filtered = {}
    for code, sig in signals.items():
        name = sig["name"]
        if "." not in name:
            filtered[code] = sig
    if len(filtered) < 5:
        filtered = signals

    ROW_H = 36
    LABEL_W = 150

    single_bit = []
    bus_signals = []
    for code, sig in filtered.items():
        if sig["width"] == 1:
            single_bit.append((code, sig))
        else:
            bus_signals.append((code, sig))
    ordered = single_bit + bus_signals

    sig_data = []
    for code, sig in ordered:
        vals = sorted(sig["values"], key=lambda x: x[0])
        disp_name = sig["name"]
        w = sig["width"]
        trans = []
        for t, v in vals:
            if w == 1:
                trans.append((t, "1" if v in ("1",) else "0"))
            else:
                binary_str = v
                try:
                    if binary_str.replace("0", "").replace("1", "") == "":
                        hex_val = format(int(binary_str, 2), "X")
                    else:
                        hex_val = binary_str
                except:
                    hex_val = binary_str
                trans.append((t, hex_val))
        raw_trans = []
        for t2, v2 in vals:
            if w == 1:
                raw_trans.append((t2, "1" if v2 in ("1",) else "0"))
            else:
                raw_trans.append((t2, v2))
        sig_data.append({"name": disp_name, "width": w, "trans": trans, "raw": raw_trans})

    sig_json = json.dumps(sig_data)
    num_sigs = len(sig_data)

    JS_CODE = r"""
let sigData = SIG_DATA_PLACEHOLDER;
let maxTime = MAX_TIME_PLACEHOLDER;
const ROW_H = ROW_H_PLACEHOLDER;
const LABEL_W = LABEL_W_PLACEHOLDER;
let zoom = 100;
let theme = 'light';
let annotations = [];
let annId = 0;
// Standalone mode: if no embedded sigData, show file picker
let isStandalone = sigData.length === 0;
// Radix for all bus signals
let busRadix = 2; // 2, 8, 10, 16
const radixLabels = {2:'BIN', 8:'OCT', 10:'DEC', 16:'HEX'};

function fmtBus(binStr) {
  if (!binStr || binStr.replace(/0/g,'').replace(/1/g,'') !== '') return binStr;
  try {
    var dec = parseInt(binStr, 2);
    if (busRadix === 8) return dec.toString(8);
    if (busRadix === 10) return dec.toString(10);
    if (busRadix === 16) return dec.toString(16).toUpperCase();
    return binStr; // bin
  } catch(e) { return binStr; }
}

function cycleRadix() {
  var order = [2, 8, 10, 16];
  for (var i = 0; i < order.length; i++) {
    if (order[i] === busRadix) {
      busRadix = order[(i + 1) % order.length];
      break;
    }
  }
  document.getElementById('radixBtn').textContent = radixLabels[busRadix];
  draw();
}
// Cursors for measurement
let cursors = []; // {time, color, label}
let activeCursor = null;
let isDraggingCursor = false;
// Compare mode
let compareData = null;
let compareMaxTime = 0;
let showCompare = false;

function pp() { return (maxTime * 0.003 * zoom / 100) / maxTime; }

function fmtTime(t) {
  if (t < 1000) return t + 'ps';
  if (t < 1000000) return (t/1000).toFixed(t%1000?1:0) + 'ns';
  if (t < 1000000000) return (t/1000000).toFixed(t%1000000?2:0) + 'us';
  return (t/1000000000).toFixed(2) + 'ms';
}

function draw() {
  var svg = document.getElementById('waveSvg');
  var baseW = maxTime * 0.003;
  var w = baseW * zoom / 100;
  var totalH = (showCompare ? sigData.length * 2 : sigData.length) * ROW_H + 28;
  var W2 = Math.max(w + LABEL_W + 40, 900);
  svg.setAttribute('width', W2);
  svg.setAttribute('viewBox', '0 0 ' + W2 + ' ' + (totalH + 20));
  var px = pp();

  var bg = theme==='dark'?'#1a1a2e':'#fafafa';
  var gridC = theme==='dark'?'#2a2a4e':'#f0f0f0';
  var textC = theme==='dark'?'#e0e0e0':'#2c3e50';
  var busF = theme==='dark'?'#1a3a2e':'#d5f4e6';
  var busS = theme==='dark'?'#2ecc71':'#27ae60';
  var busT = theme==='dark'?'#2ecc71':'#1a7a4a';

  document.body.style.background = bg;
  document.getElementById('toolbar').style.background = theme==='dark'?'#16213e':'#fff';

  var html = '<rect width="100%" height="100%" fill="' + bg + '"/>';

  // Time axis band
  html += '<rect x="0" y="0" width="100%" height="26" fill="' + (theme==='dark'?'#0f3460':'#dfe6e9') + '"/>';
  var gridStep = 1;
  if (maxTime > 1000) gridStep = 10;
  if (maxTime > 10000) gridStep = 100;
  if (maxTime > 100000) gridStep = 1000;
  if (maxTime > 1000000) gridStep = 10000;
  if (maxTime > 10000000) gridStep = 100000;

  for (var t = 0; t <= maxTime; t += gridStep) {
    var x = t * px + LABEL_W;
    html += '<line x1="' + x + '" y1="26" x2="' + x + '" y2="' + (showCompare?totalH-20:totalH) + '" stroke="' + gridC + '" stroke-width="1"/>';
    var show = (maxTime/gridStep < 40) || (t % (gridStep*5) === 0);
    if (show) {
      html += '<text x="' + (x+2) + '" y="17" font-size="10" fill="' + (theme==='dark'?'#fff':'#2d3436') + '">' + fmtTime(t) + '</text>';
    }
  }

  // Draw signal group
  function drawSignals(data, offset, suffix, colorShift) {
    for (var i = 0; i < data.length; i++) {
      var sig = data[i];
      var y0 = i * ROW_H + offset;
      var isBus = sig.width > 1;
      var rowBg = i%2===0 ? 'transparent' : (theme==='dark'?'rgba(255,255,255,0.03)':'rgba(0,0,0,0.02)');
      html += '<rect x="0" y="' + y0 + '" width="100%" height="' + ROW_H + '" fill="' + rowBg + '"/>';
      var lc = isBus?'#3498db':textC;
      var dn = sig.name;
      if (suffix) dn += ' ' + suffix;
      html += '<text x="8" y="' + (y0+ROW_H/2+4) + '" font-size="11" font-weight="600" fill="' + lc + '">' + dn + '</text>';
      if (suffix) {
        html += '<rect x="' + (LABEL_W-20) + '" y="' + (y0+ROW_H/2-10) + '" width="14" height="14" rx="2" fill="' + colorShift + '"/>';
      }
      var trans = sig.trans;
      if (!trans||trans.length===0) continue;
      var prevT = trans[0][0], prevV = trans[0][1];
      var sc = suffix ? '#e17055' : textC;
      for (var j=0; j<trans.length; j++) {
        var t = trans[j][0], v = trans[j][1];
        var x1 = prevT*px+LABEL_W, x2 = t*px+LABEL_W;
        if (isBus) {
          html += '<rect x="' + x1 + '" y="' + (y0+4) + '" width="' + Math.max(4,x2-x1) + '" height="' + (ROW_H-8) + '" fill="' + (suffix?'#fef3e2':busF) + '" stroke="' + (suffix?'#e17055':busS) + '" stroke-width="0.5" rx="2"/>';
          if (x2-x1>20) { var rv = sig.raw && sig.raw[j] ? sig.raw[j][1] : prevV; html += '<text x="' + (x1+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="10" font-family="Consolas" fill="' + (suffix?'#d35400':busT) + '">' + fmtBus(rv) + '</text>'; }
        } else {
          var lvl = y0 + (prevV==='1'?6:ROW_H-6);
          html += '<line x1="' + x1 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + lvl + '" stroke="' + sc + '" stroke-width="1.5"/>';
          if (v!==prevV) { var nl = y0+(v==='1'?6:ROW_H-6); html += '<line x1="' + x2 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + nl + '" stroke="' + sc + '" stroke-width="1.5"/>'; }
        }
        prevT=t; prevV=v;
      }
      var xEnd = maxTime*px+LABEL_W;
      if (isBus) {
        html += '<rect x="' + (prevT*px+LABEL_W) + '" y="' + (y0+4) + '" width="' + Math.max(4,xEnd-prevT*px-LABEL_W) + '" height="' + (ROW_H-8) + '" fill="' + (suffix?'#fef3e2':busF) + '" stroke="' + (suffix?'#e17055':busS) + '" stroke-width="0.5" rx="2"/>';
        if (xEnd-prevT*px-LABEL_W>20) { var lrv = sig.raw && sig.raw[sig.raw.length-1] ? sig.raw[sig.raw.length-1][1] : prevV; html += '<text x="' + (prevT*px+LABEL_W+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="10" font-family="Consolas" fill="' + (suffix?'#d35400':busT) + '">' + fmtBus(lrv) + '</text>'; }
      } else {
        var lvl = y0+(prevV==='1'?6:ROW_H-6);
        html += '<line x1="' + (prevT*px+LABEL_W) + '" y1="' + lvl + '" x2="' + xEnd + '" y2="' + lvl + '" stroke="' + sc + '" stroke-width="1.5"/>';
      }
    }
  }

  drawSignals(sigData, 28, '', textC);
  if (showCompare && compareData) {
    // Separator line
    var sepY = sigData.length * ROW_H + 28 + 4;
    html += '<line x1="0" y1="' + sepY + '" x2="' + W2 + '" y2="' + sepY + '" stroke="#3498db" stroke-width="2" stroke-dasharray="8,4"/>';
    html += '<text x="8" y="' + (sepY+12) + '" font-size="10" fill="#3498db" font-weight="bold">Compare</text>';
    drawSignals(compareData, sepY + 8, '[2]', '#e17055');
  }

  // Cursors (measurement)
  for (var c=0; c<cursors.length; c++) {
    var cur = cursors[c];
    var cx = cur.time * px + LABEL_W;
    html += '<line x1="' + cx + '" y1="0" x2="' + cx + '" y2="' + totalH + '" stroke="' + cur.color + '" stroke-width="2" stroke-dasharray="5,3"/>';
    html += '<rect x="' + (cx-28) + '" y="0" width="56" height="18" rx="3" fill="' + cur.color + '"/>';
    html += '<text x="' + cx + '" y="13" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">' + cur.label + '</text>';
    html += '<polygon points="' + (cx-7) + ',' + (totalH-2) + ' ' + (cx+7) + ',' + (totalH-2) + ' ' + cx + ',' + (totalH+6) + '" fill="' + cur.color + '"/>';
  }

  // Show measurement delta
  if (cursors.length >= 2) {
    var tA = cursors[0].time, tB = cursors[1].time;
    var dt = Math.abs(tB - tA);
    var midX = ((tA + tB)/2) * px + LABEL_W;
    html += '<rect x="' + (midX-60) + '" y="28" width="120" height="20" rx="4" fill="#2d3436" opacity="0.85"/>';
    html += '<text x="' + midX + '" y="42" text-anchor="middle" font-size="12" font-weight="bold" fill="#fff">Δt = ' + fmtTime(dt) + '</text>';
  }

  // Markers from annotations
  for (var m=0; m<annotations.length; m++) {
    var mx = annotations[m].time * px + LABEL_W;
    html += '<line x1="' + mx + '" y1="26" x2="' + mx + '" y2="' + totalH + '" stroke="#e17055" stroke-width="1.5" stroke-dasharray="4,3"/>';
  }

  svg.innerHTML = html;
}

// ===== Annotation Panel =====
function renderAnnPanel() {
  var panel = document.getElementById('annPanel');
  panel.style.background = theme==='dark'?'#16213e':'#fff';
  if (annotations.length === 0 && cursors.length === 0) {
    panel.innerHTML = '<div class="ann-empty">Click to place cursor | Add cursors for measurement | Add notes</div>';
    return;
  }
  var h = '<table><tr><th>Time</th><th>Label</th><th></th></tr>';
  // Cursors first
  for (var i=0; i<cursors.length; i++) {
    var c = cursors[i];
    h += '<tr><td class="ann-time" style="color:' + c.color + '">' + fmtTime(c.time) + '</td><td class="ann-text">[' + c.label + '] Cursor</td><td class="ann-del"><button onclick="delCursor(' + i + ')" class="del-btn">\u2715</button></td></tr>';
  }
  if (cursors.length >= 2) {
    var dt = Math.abs(cursors[0].time - cursors[1].time);
    h += '<tr style="background:' + (theme==='dark'?'#0f3460':'#dfe6e9') + '"><td class="ann-time" style="color:#2d3436;font-weight:bold" colspan="2">\u0394t = ' + fmtTime(dt) + '</td><td></td></tr>';
  }
  for (var i=0; i<annotations.length; i++) {
    var a = annotations[i];
    h += '<tr><td class="ann-time">' + fmtTime(a.time) + '</td><td class="ann-text">' + a.label + '</td><td class="ann-del"><button onclick="delAnn(' + i + ')" class="del-btn">\u2715</button></td></tr>';
  }
  h += '</table>';
  panel.innerHTML = h;
}

function delAnn(idx) { annotations.splice(idx,1); renderAnnPanel(); draw(); }
function delCursor(idx) { cursors.splice(idx,1); renderAnnPanel(); draw(); }

// Zoom
function zoomIn() { zoom=Math.min(500,zoom*1.5); zoomUpdate(); }
function zoomOut() { zoom=Math.max(10,zoom/1.5); zoomUpdate(); }
function zoomReset() { zoom=100; zoomUpdate(); }
function zoomSet(v) { zoom=parseInt(v); zoomUpdate(); }
function zoomUpdate() {
  document.getElementById('zoomSlider').value=zoom;
  document.getElementById('zoomLabel').textContent=zoom+'%';
  draw();
}
function scrollLeft() { document.getElementById('waveContainer').scrollLeft-=200; }
function scrollRight() { document.getElementById('waveContainer').scrollLeft+=200; }

function toggleTheme() {
  theme=theme==='dark'?'light':'dark';
  document.getElementById('themeBtn').textContent=theme==='dark'?'☀ Light':'🌙 Dark';
  draw(); renderAnnPanel();
}

function getTimeFromClick(e) {
  var container = document.getElementById('waveContainer');
  var rect = container.getBoundingClientRect();
  var clickX = e.clientX - rect.left + container.scrollLeft - LABEL_W;
  if (clickX < 0) clickX = 0;
  var t = Math.round(clickX / pp());
  return Math.max(0, Math.min(maxTime, t));
}

// SVG click: place or select cursor
document.addEventListener('DOMContentLoaded', function() {
  var svg = document.getElementById('waveSvg');
  svg.addEventListener('click', function(e) {
    var t = getTimeFromClick(e);
    // Check if clicking near existing cursor
    for (var i=0; i<cursors.length; i++) {
      var pxVal = pp();
      var cx = cursors[i].time * pxVal + LABEL_W;
      var rect = document.getElementById('waveContainer');
      var clickX = e.clientX - rect.getBoundingClientRect().left + rect.scrollLeft;
      if (Math.abs(clickX - cx) < 12) {
        activeCursor = i;
        return;
      }
    }
    // Otherwise place new cursor (max 2)
    if (cursors.length >= 2) cursors.shift();
    var idx = cursors.length;
    var colors = ['#e74c3c','#3498db','#2ecc71'];
    var labels = ['A','B','C'];
    cursors.push({time:t, color:colors[idx], label:labels[idx]});
    activeCursor = cursors.length - 1;
    renderAnnPanel();
    draw();
  });
});

// Drag cursors
(function() {
  var svg = document.getElementById('waveSvg');
  svg.addEventListener('mousedown', function(e) {
    if (cursors.length === 0) return;
    var pxVal = pp();
    var rect = document.getElementById('waveContainer');
    var clickX = e.clientX - rect.getBoundingClientRect().left + rect.scrollLeft;
    for (var i=0; i<cursors.length; i++) {
      var cx = cursors[i].time * pxVal + LABEL_W;
      if (Math.abs(clickX - cx) < 15) {
        activeCursor = i;
        isDraggingCursor = true;
        e.preventDefault();
        return;
      }
    }
  });
  document.addEventListener('mousemove', function(e) {
    if (!isDraggingCursor || activeCursor === null) return;
    var t = getTimeFromClick(e);
    cursors[activeCursor].time = t;
    renderAnnPanel();
    draw();
  });
  document.addEventListener('mouseup', function() { isDraggingCursor = false; activeCursor = null; });
})();

function addNote() {
  if (cursors.length === 0) { alert('Click waveform to place cursor A first!'); return; }
  var t = cursors[cursors.length-1].time;
  var text = prompt('Annotation at ' + fmtTime(t) + ':');
  if (!text) return;
  annotations.push({time:t, label:text});
  renderAnnPanel();
  draw();
}

function clearAnns() {
  if (!confirm('Clear all cursors, markers and annotations?')) return;
  cursors = []; annotations = [];
  renderAnnPanel(); draw();
}

function clearCursors() {
  cursors = [];
  renderAnnPanel(); draw();
}

// Minimal VCD parser in JS
function parseVCD(text) {
  var signals = {};
  var scopeStack = [''];
  var maxTime = 0;
  var currentTime = 0;
  var lines = text.split('\n');
  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].trim();
    if (line.startsWith('$scope')) {
      var parts = line.split(/\s+/);
      if (parts.length >= 3) scopeStack.push(parts[2]);
    } else if (line.startsWith('$upscope')) {
      if (scopeStack.length > 1) scopeStack.pop();
    } else if (line.startsWith('$var')) {
      var parts = line.split(/\s+/);
      if (parts.length >= 5) {
        var w = parseInt(parts[2]), code = parts[3], name = parts[4];
        var full = scopeStack[scopeStack.length-1] ? scopeStack[scopeStack.length-1]+'.'+name : name;
        signals[code] = {name: full, width: w, values: []};
      }
    } else if (line.startsWith('#') && /^\d+$/.test(line.substring(1))) {
      currentTime = parseInt(line.substring(1));
      maxTime = Math.max(maxTime, currentTime);
    } else if (line.startsWith('b')) {
      var parts = line.split(/\s+/);
      if (parts.length >= 2 && signals[parts[1]]) {
        signals[parts[1]].values.push([currentTime, parts[0].substring(1)]);
      }
    } else if (line.length >= 2 && '01xzXZ'.includes(line[0]) && signals[line.substring(1)]) {
      signals[line.substring(1)].values.push([currentTime, line[0]]);
    }
  }
  // Convert to array format
  var result = [];
  for (var code in signals) {
    var sig = signals[code];
    var name = sig.name.split('.').pop();
    var w = sig.width;
    var vals = sig.values.sort(function(a,b){return a[0]-b[0];});
    var trans = [];
    for (var j=0; j<vals.length; j++) {
      var t = vals[j][0], v = vals[j][1];
      if (w === 1) {
        trans.push([t, (v==='1'||v==='1')?'1':'0']);
      } else {
        var hv = v;
        try { if (v.replace(/0/g,'').replace(/1/g,'')==='') hv = parseInt(v,2).toString(16).toUpperCase(); } catch(e) {}
        trans.push([t, hv]);
      }
    }
    result.push({name:name, width:w, trans:trans});
  }
  return {signals:result, maxTime:maxTime};
}

function loadCompare() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = '.vcd';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {
      try {
        var d = parseVCD(ev.target.result);
        if (!d.signals || d.signals.length === 0) { alert('No signals found in VCD'); return; }
        compareData = d.signals;
        compareMaxTime = d.maxTime;
        showCompare = true;
        document.getElementById('compareBtn').textContent = '\u274c Remove Compare';
        draw();
      } catch(ex) { alert('Parse error: ' + ex.message); }
    };
    reader.readAsText(file);
  };
  input.click();
}

function openVCD() {
  var input = document.createElement('input');
  input.type = 'file';
  input.accept = '.vcd';
  input.onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {
      try {
        var d = parseVCD(ev.target.result);
        if (!d.signals || d.signals.length === 0) { alert('No signals found'); return; }
        // Replace sigData with loaded data
        sigData.length = 0;
        for (var i = 0; i < d.signals.length; i++) sigData.push(d.signals[i]);
        maxTime = d.maxTime;
        isStandalone = false;
        cursors = []; annotations = []; showCompare = false;
        document.getElementById('openBtn').textContent = '\ud83d\udcc2 ' + file.name;
        document.getElementById('welcome').style.display = 'none';
        document.querySelector('.wave-container').style.display = 'block';
        document.getElementById('toolbar').style.display = 'flex';
        document.getElementById('annPanel').style.display = 'block';
        draw();
        renderAnnPanel();
      } catch(ex) { alert('Parse error: ' + ex.message); }
    };
    reader.readAsText(file);
  };
  input.click();
}

function toggleCompare() {
  if (showCompare) {
    showCompare = false;
    compareData = null;
    document.getElementById('compareBtn').textContent = '\u2194 Compare';
    draw();
  } else {
    loadCompare();
  }
}

function exportPNG() {
  var svg = document.getElementById('waveSvg');
  var w = parseFloat(svg.getAttribute('width')) || 1200;
  var viewBox = svg.getAttribute('viewBox');
  var parts = viewBox ? viewBox.split(/\s+/).map(parseFloat) : [0,0,w,600];
  var vw = parts[2] || w, vh = parts[3] || 600;
  var scale = 2;
  var cw = Math.round(vw * scale), ch = Math.round(vh * scale);
  var data = (new XMLSerializer()).serializeToString(svg);
  var blob = new Blob([data], {type:'image/svg+xml;charset=utf-8'});
  var url = URL.createObjectURL(blob);
  var canvas = document.createElement('canvas');
  canvas.width = cw; canvas.height = ch;
  var ctx = canvas.getContext('2d');
  ctx.scale(scale, scale);
  ctx.fillStyle = theme==='dark'?'#1a1a2e':'#fafafa';
  ctx.fillRect(0,0,vw,vh);
  var img = new Image();
  img.onload = function() {
    ctx.drawImage(img,0,0,vw,vh);
    URL.revokeObjectURL(url);
    canvas.toBlob(function(b) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(b);
      a.download = 'waveform.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    },'image/png');
  };
  img.onerror = function() { alert('PNG export failed - try SVG export instead.'); };
  img.src = url;
}

function exportSVG() {
  var svg = document.getElementById('waveSvg');
  var s = (new XMLSerializer()).serializeToString(svg);
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([s],{type:'image/svg+xml'}));
  a.download = 'waveform.svg'; a.click();
}

// Drag & drop VCD files
document.addEventListener('dragover', function(e) { e.preventDefault(); });
document.addEventListener('drop', function(e) {
  e.preventDefault();
  var file = e.dataTransfer.files[0];
  if (!file || !file.name.endsWith('.vcd')) { alert('Please drop a .vcd file'); return; }
  var reader = new FileReader();
  reader.onload = function(ev) {
    try {
      var d = parseVCD(ev.target.result);
      if (!d.signals || d.signals.length === 0) { alert('No signals found'); return; }
      sigData.length = 0;
      for (var i = 0; i < d.signals.length; i++) sigData.push(d.signals[i]);
      maxTime = d.maxTime;
      isStandalone = false;
      cursors = []; annotations = []; showCompare = false;
      document.getElementById('openBtn').textContent = '\ud83d\udcc2 ' + file.name;
      document.getElementById('welcome').style.display = 'none';
      document.querySelector('.wave-container').style.display = 'block';
      document.getElementById('toolbar').style.display = 'flex';
      document.getElementById('annPanel').style.display = 'block';
      draw();
      renderAnnPanel();
    } catch(ex) { alert('Parse error: ' + ex.message); }
  };
  reader.readAsText(file);
});

// Drag scroll
(function() {
  var c = document.getElementById('waveContainer');
  var down=false, sx, sl;
  c.onmousedown = function(e) { if (isDraggingCursor) return; down=true; sx=e.pageX-c.offsetLeft; sl=c.scrollLeft; };
  c.onmouseleave = function() { down=false; };
  c.onmouseup = function() { down=false; };
  c.onmousemove = function(e) { if (!down||isDraggingCursor) return; e.preventDefault(); c.scrollLeft=sl-(e.pageX-c.offsetLeft-sx)*1.5; };
})();

draw();
renderAnnPanel();
"""

    JS_CODE = JS_CODE.replace("SIG_DATA_PLACEHOLDER", sig_json)
    JS_CODE = JS_CODE.replace("MAX_TIME_PLACEHOLDER", str(max_time))
    JS_CODE = JS_CODE.replace("ROW_H_PLACEHOLDER", str(ROW_H))
    JS_CODE = JS_CODE.replace("LABEL_W_PLACEHOLDER", str(LABEL_W))

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{title}</title>
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{font-family:'Segoe UI','Consolas',monospace;background:#fafafa;color:#2c3e50;height:100vh;display:flex;flex-direction:column}}
.toolbar {{flex-shrink:0;background:#fff;border-bottom:2px solid #3498db;
  padding:5px 10px;display:flex;align-items:center;gap:4px;flex-wrap:wrap}}
.toolbar .title {{font-size:14px;font-weight:bold;color:#2c3e50;margin-right:10px}}
.toolbar .info {{font-size:11px;color:#7f8c8d;margin-right:auto}}
.toolbar button {{padding:4px 7px;border:1px solid #bdc3c7;border-radius:3px;background:#fff;
  cursor:pointer;font-size:11px;color:#2c3e50;user-select:none}}
.toolbar button:hover {{background:#ecf0f1;border-color:#3498db}}
.toolbar button.primary {{background:#3498db;color:#fff;border-color:#3498db}}
.toolbar button.primary:hover {{background:#2980b9}}
.toolbar button.danger {{background:#e74c3c;color:#fff;border-color:#e74c3c}}
.toolbar button.danger:hover {{background:#c0392b}}
.toolbar button.compare {{background:#e17055;color:#fff;border-color:#e17055}}
.toolbar button.compare:hover {{background:#d35400}}
.toolbar input[type=range] {{width:70px;vertical-align:middle}}
.zoom-label {{font-size:11px;color:#7f8c8d;min-width:28px;text-align:center}}
.sep {{width:1px;height:18px;background:#ddd;margin:0 2px}}
.wave-container {{overflow-x:auto;overflow-y:hidden;cursor:grab;flex:1 1 auto}}
.wave-container:active {{cursor:grabbing}}
.wave-inner svg {{display:block}}
#annPanel {{flex-shrink:0;max-height:180px;overflow-y:auto;background:#fff;border-top:1px solid #dfe6e9;padding:3px 10px}}
#annPanel table {{width:100%;border-collapse:collapse;font-size:12px}}
#annPanel th {{text-align:left;padding:3px 6px;color:#7f8c8d;font-weight:600;font-size:11px;border-bottom:1px solid #dfe6e9;position:sticky;top:0;background:#fff}}
#annPanel td {{padding:3px 6px;border-bottom:1px solid #f0f0f0}}
#annPanel .ann-time {{font-weight:600;font-family:Consolas;width:90px}}
#annPanel .ann-text {{color:#2c3e50}}
#annPanel .ann-del {{width:24px;text-align:center}}
#annPanel .ann-empty {{padding:8px 6px;color:#95a5a6;font-size:11px;text-align:center}}
.del-btn {{background:none;border:none;color:#e74c3c;cursor:pointer;font-size:13px;padding:0 3px}}
.del-btn:hover {{color:#c0392b}}
.footer {{flex-shrink:0;text-align:center;padding:3px;font-size:10px;color:#95a5a6;border-top:1px solid #eee}}

/* Welcome screen */
.welcome {{display:flex;align-items:center;justify-content:center;flex:1;background:#fafafa}}
.welcome-box {{text-align:center;padding:60px}}
.welcome-icon {{font-size:64px;margin-bottom:16px}}
.welcome-box h2 {{font-size:28px;color:#2c3e50;margin-bottom:8px}}
.welcome-box p {{font-size:14px;color:#7f8c8d;margin-bottom:24px}}
.welcome-btn {{padding:14px 32px;font-size:16px;background:#3498db;color:#fff;border:none;border-radius:8px;cursor:pointer}}
.welcome-btn:hover {{background:#2980b9}}
.welcome-hint {{font-size:12px !important;color:#95a5a6 !important;margin-top:16px !important}}
</style>
</head><body>

<div class="welcome" id="welcome">
  <div class="welcome-box">
    <div class="welcome-icon">&#128187;</div>
    <h2>vcd2wave</h2>
    <p>Visualize VCD waveform files in your browser</p>
    <button class="welcome-btn" onclick="openVCD()">&#128194; Open VCD File</button>
    <p class="welcome-hint">Or drag & drop a .vcd file anywhere on this page</p>
  </div>
</div>

<div class="toolbar" id="toolbar" style="display:{'none' if num_sigs == 0 else 'flex'}">
  <span class="title">{title}</span>
  <span class="info">{num_sigs} signals | {max_time} ps</span>
  <button id="openBtn" onclick="openVCD()">&#128194; Open</button>
  <button id="radixBtn" onclick="cycleRadix()" class="primary">BIN</button>
  <div class="sep"></div>
  <button onclick="zoomIn()">[+]</button>
  <span class="zoom-label" id="zoomLabel">100%</span>
  <button onclick="zoomOut()">[-]</button>
  <button onclick="zoomReset()">Reset</button>
  <input type="range" id="zoomSlider" min="10" max="500" value="100" oninput="zoomSet(this.value)">
  <div class="sep"></div>
  <button onclick="scrollLeft()">&lt;</button>
  <button onclick="scrollRight()">&gt;</button>
  <div class="sep"></div>
  <button id="themeBtn" onclick="toggleTheme()">&#127769; Dark</button>
  <button onclick="addNote()">&#128221; Note</button>
  <button onclick="clearCursors()" class="danger">&#10005; Cursors</button>
  <button onclick="clearAnns()" class="danger">&#10005; All</button>
  <div class="sep"></div>
  <button class="primary" onclick="exportPNG()">&#128190; PNG</button>
  <button onclick="exportSVG()">SVG</button>
  <div class="sep"></div>
  <button class="compare" id="compareBtn" onclick="toggleCompare()">&#2194; Compare</button>
</div>

<div class="wave-container" id="waveContainer" style="display:{'none' if num_sigs == 0 else 'block'}">
  <div class="wave-inner">
    <svg id="waveSvg"></svg>
  </div>
</div>

<div id="annPanel" style="display:{'none' if num_sigs == 0 else 'block'}"><div class="ann-empty">Click waveform to place cursors A & B | Drag to measure | Add notes</div></div>

<div class="footer">Click waveform to place cursor | Two cursors = &#916;t measurement | Compare: load another VCD</div>
<script>{JS_CODE}</script>
</body></html>"""

    return html
