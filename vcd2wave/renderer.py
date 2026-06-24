"""HTML waveform renderer with annotation panel, markers, export."""


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
        if sig['width'] == 1:
            single_bit.append((code, sig))
        else:
            bus_signals.append((code, sig))
    ordered = single_bit + bus_signals

    sig_data = []
    for code, sig in ordered:
        vals = sorted(sig['values'], key=lambda x: x[0])
        disp_name = sig['name'].split('.')[-1]
        w = sig['width']
        trans = []
        for t, v in vals:
            if w == 1:
                trans.append((t, '1' if v in ('1',) else '0'))
            else:
                binary_str = v
                try:
                    if binary_str.replace('0','').replace('1','') == '':
                        hex_val = format(int(binary_str, 2), 'X')
                    else:
                        hex_val = binary_str
                except:
                    hex_val = binary_str
                trans.append((t, hex_val))
        sig_data.append({'name': disp_name, 'width': w, 'trans': trans})

    import json
    sig_json = json.dumps(sig_data)
    num_sigs = len(sig_data)

    JS_CODE = r"""
const sigData = SIG_DATA_PLACEHOLDER;
const maxTime = MAX_TIME_PLACEHOLDER;
const ROW_H = ROW_H_PLACEHOLDER;
const LABEL_W = LABEL_W_PLACEHOLDER;
let zoom = 100;
let theme = 'light';
let annotations = [];
let annId = 0;
let cursorTime = -1;
let cursorVisible = false;
let isDraggingCursor = false;

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
  var totalH = sigData.length * ROW_H + 28;
  var W2 = Math.max(w + LABEL_W + 40, 900);
  svg.setAttribute('width', W2);
  svg.setAttribute('viewBox', '0 0 ' + W2 + ' ' + totalH);
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
    html += '<line x1="' + x + '" y1="26" x2="' + x + '" y2="' + totalH + '" stroke="' + gridC + '" stroke-width="1"/>';
    var show = (maxTime/gridStep < 40) || (t % (gridStep*5) === 0);
    if (show) {
      html += '<text x="' + (x+2) + '" y="17" font-size="10" fill="' + (theme==='dark'?'#fff':'#2d3436') + '">' + fmtTime(t) + '</text>';
    }
  }

  // Cursor
  if (cursorVisible && cursorTime >= 0) {
    var cx = cursorTime * px + LABEL_W;
    html += '<line x1="' + cx + '" y1="0" x2="' + cx + '" y2="' + totalH + '" stroke="#e74c3c" stroke-width="2" stroke-dasharray="5,3"/>';
    html += '<rect x="' + (cx-30) + '" y="0" width="60" height="18" rx="3" fill="#e74c3c"/>';
    html += '<text x="' + cx + '" y="13" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">' + fmtTime(cursorTime) + '</text>';
    // Drag handle
    html += '<polygon points="' + (cx-8) + ',' + (totalH-4) + ' ' + (cx+8) + ',' + (totalH-4) + ' ' + cx + ',' + totalH + '" fill="#e74c3c"/>';
  }

  // Signal rows
  for (var i = 0; i < sigData.length; i++) {
    var sig = sigData[i];
    var y0 = i * ROW_H + 28;
    var isBus = sig.width > 1;
    var rowBg = i%2===0 ? 'transparent' : (theme==='dark'?'rgba(255,255,255,0.03)':'rgba(0,0,0,0.02)');
    html += '<rect x="0" y="' + y0 + '" width="100%" height="' + ROW_H + '" fill="' + rowBg + '"/>';
    var lc = isBus?'#3498db':textC;
    html += '<text x="8" y="' + (y0+ROW_H/2+4) + '" font-size="11" font-weight="600" fill="' + lc + '">' + sig.name + '</text>';
    var trans = sig.trans;
    if (!trans||trans.length===0) continue;
    var prevT = trans[0][0], prevV = trans[0][1];
    for (var j=0; j<trans.length; j++) {
      var t = trans[j][0], v = trans[j][1];
      var x1 = prevT*px+LABEL_W, x2 = t*px+LABEL_W;
      if (isBus) {
        html += '<rect x="' + x1 + '" y="' + (y0+4) + '" width="' + Math.max(4,x2-x1) + '" height="' + (ROW_H-8) + '" fill="' + busF + '" stroke="' + busS + '" stroke-width="0.5" rx="2"/>';
        if (x2-x1>20) html += '<text x="' + (x1+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="10" font-family="Consolas" fill="' + busT + '">' + prevV + '</text>';
      } else {
        var lvl = y0 + (prevV==='1'?6:ROW_H-6);
        html += '<line x1="' + x1 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + lvl + '" stroke="' + textC + '" stroke-width="1.5"/>';
        if (v!==prevV) {
          var nl = y0 + (v==='1'?6:ROW_H-6);
          html += '<line x1="' + x2 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + nl + '" stroke="' + textC + '" stroke-width="1.5"/>';
        }
      }
      prevT=t; prevV=v;
    }
    var xEnd = maxTime*px+LABEL_W;
    if (isBus) {
      html += '<rect x="' + (prevT*px+LABEL_W) + '" y="' + (y0+4) + '" width="' + Math.max(4,xEnd-prevT*px-LABEL_W) + '" height="' + (ROW_H-8) + '" fill="' + busF + '" stroke="' + busS + '" stroke-width="0.5" rx="2"/>';
      if (xEnd-prevT*px-LABEL_W>20) html += '<text x="' + (prevT*px+LABEL_W+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="10" font-family="Consolas" fill="' + busT + '">' + prevV + '</text>';
    } else {
      var lvl = y0 + (prevV==='1'?6:ROW_H-6);
      html += '<line x1="' + (prevT*px+LABEL_W) + '" y1="' + lvl + '" x2="' + xEnd + '" y2="' + lvl + '" stroke="' + textC + '" stroke-width="1.5"/>';
    }
  }

  // === MARKERS: only vertical line, NO text on waveform ===
  for (var m=0; m<annotations.length; m++) {
    var mx = annotations[m].time * px + LABEL_W;
    html += '<line x1="' + mx + '" y1="26" x2="' + mx + '" y2="' + totalH + '" stroke="#e17055" stroke-width="1.5" stroke-dasharray="4,3"/>';
  }

  svg.innerHTML = html;
}

// ===== Annotation Panel (below waveform, no overlap) =====
function renderAnnPanel() {
  var panel = document.getElementById('annPanel');
  var isDark = theme==='dark';
  panel.style.background = isDark?'#16213e':'#fff';
  panel.style.borderTop = '1px solid ' + (isDark?'#0f3460':'#dfe6e9');

  if (annotations.length === 0) {
    panel.innerHTML = '<div class="ann-empty">Click waveform to place cursor, then add notes</div>';
    return;
  }
  var h = '<table><tr><th>Time</th><th>Annotation</th><th></th></tr>';
  for (var i=0; i<annotations.length; i++) {
    var a = annotations[i];
    h += '<tr><td class="ann-time">' + fmtTime(a.time) + '</td><td class="ann-text">' + a.label + '</td>';
    h += '<td class="ann-del"><button onclick="delAnn(' + i + ')" class="del-btn">✕</button></td></tr>';
  }
  h += '</table>';
  panel.innerHTML = h;
}

function delAnn(idx) {
  annotations.splice(idx, 1);
  renderAnnPanel();
  draw();
}

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
  draw();
  renderAnnPanel();
}

function getTimeFromClick(e) {
  var container = document.getElementById('waveContainer');
  var rect = container.getBoundingClientRect();
  var clickX = e.clientX - rect.left + container.scrollLeft - LABEL_W;
  var px = pp();
  if (clickX < 0) clickX = 0;
  var t = Math.round(clickX / px);
  return Math.max(0, Math.min(maxTime, t));
}

// Click on SVG to place cursor
document.addEventListener('DOMContentLoaded', function() {
  var svg = document.getElementById('waveSvg');
  svg.addEventListener('click', function(e) {
    cursorTime = getTimeFromClick(e);
    cursorVisible = true;
    document.getElementById('cursorInfo').textContent = fmtTime(cursorTime);
    draw();
  });
});

// Drag cursor
(function() {
  var svg = document.getElementById('waveSvg');
  svg.addEventListener('mousedown', function(e) {
    if (!cursorVisible) return;
    var px = pp();
    var cx = cursorTime * px + LABEL_W;
    var rect = document.getElementById('waveContainer');
    var clickX = e.clientX - rect.getBoundingClientRect().left + rect.scrollLeft;
    if (Math.abs(clickX - cx) < 15) {
      isDraggingCursor = true;
      e.preventDefault();
    }
  });
  document.addEventListener('mousemove', function(e) {
    if (!isDraggingCursor) return;
    cursorTime = getTimeFromClick(e);
    document.getElementById('cursorInfo').textContent = fmtTime(cursorTime);
    draw();
  });
  document.addEventListener('mouseup', function() { isDraggingCursor = false; });
})();

function addNote() {
  if (!cursorVisible || cursorTime < 0) { alert('Click on the waveform to place cursor first!'); return; }
  var text = prompt('Annotation:');
  if (!text) return;
  annotations.push({time:cursorTime, label:text});
  renderAnnPanel();
  draw();
}

function clearAnns() {
  if (!confirm('Clear all annotations?')) return;
  annotations = [];
  renderAnnPanel();
  draw();
}

function exportPNG() {
  var svg = document.getElementById('waveSvg');
  var data = (new XMLSerializer()).serializeToString(svg);
  var canvas = document.createElement('canvas');
  canvas.width = 1920; canvas.height = 1080;
  var ctx = canvas.getContext('2d');
  ctx.fillStyle = theme==='dark'?'#1a1a2e':'#fafafa';
  ctx.fillRect(0,0,canvas.width,canvas.height);
  var img = new Image();
  img.onload = function() {
    ctx.drawImage(img,0,0,canvas.width,canvas.height);
    canvas.toBlob(function(b) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(b); a.download = 'waveform.png'; a.click();
    },'image/png');
  };
  img.src = URL.createObjectURL(new Blob([data],{type:'image/svg+xml'}));
}

function exportSVG() {
  var svg = document.getElementById('waveSvg');
  var s = (new XMLSerializer()).serializeToString(svg);
  var a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([s],{type:'image/svg+xml'}));
  a.download = 'waveform.svg'; a.click();
}

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
  padding:5px 12px;display:flex;align-items:center;gap:5px;flex-wrap:wrap}}
.toolbar .title {{font-size:14px;font-weight:bold;color:#2c3e50;margin-right:12px}}
.toolbar .info {{font-size:11px;color:#7f8c8d;margin-right:auto}}
.toolbar button {{padding:4px 8px;border:1px solid #bdc3c7;border-radius:3px;background:#fff;
  cursor:pointer;font-size:11px;color:#2c3e50;user-select:none}}
.toolbar button:hover {{background:#ecf0f1;border-color:#3498db}}
.toolbar button.primary {{background:#3498db;color:#fff;border-color:#3498db}}
.toolbar button.primary:hover {{background:#2980b9}}
.toolbar button.danger {{background:#e74c3c;color:#fff;border-color:#e74c3c}}
.toolbar button.danger:hover {{background:#c0392b}}
.toolbar input[type=range] {{width:80px;vertical-align:middle}}
.zoom-label {{font-size:11px;color:#7f8c8d;min-width:30px;text-align:center}}
.sep {{width:1px;height:20px;background:#ddd;margin:0 3px}}
#cursorInfo {{font-size:11px;color:#e74c3c;font-weight:bold;min-width:80px}}

.wave-container {{overflow-x:auto;overflow-y:hidden;cursor:grab;flex:1 1 auto}}
.wave-container:active {{cursor:grabbing}}
.wave-inner svg {{display:block}}

#annPanel {{flex-shrink:0;max-height:200px;overflow-y:auto;background:#fff;border-top:1px solid #dfe6e9;padding:4px 12px}}
#annPanel table {{width:100%;border-collapse:collapse;font-size:12px}}
#annPanel th {{text-align:left;padding:4px 6px;color:#7f8c8d;font-weight:600;font-size:11px;
  border-bottom:1px solid #dfe6e9;position:sticky;top:0;background:#fff}}
#annPanel td {{padding:4px 6px;border-bottom:1px solid #f0f0f0}}
#annPanel .ann-time {{color:#e74c3c;font-weight:600;font-family:Consolas;width:100px}}
#annPanel .ann-text {{color:#2c3e50}}
#annPanel .ann-del {{width:30px;text-align:center}}
#annPanel .ann-empty {{padding:12px 6px;color:#95a5a6;font-size:12px;text-align:center}}
.del-btn {{background:none;border:none;color:#e74c3c;cursor:pointer;font-size:14px;padding:0 4px}}
.del-btn:hover {{color:#c0392b}}

.footer {{flex-shrink:0;text-align:center;padding:4px;font-size:10px;color:#95a5a6;border-top:1px solid #eee}}
</style>
</head><body>

<div class="toolbar" id="toolbar">
  <span class="title">{title}</span>
  <span class="info">{num_sigs} signals | {max_time} ps</span>
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
  <button onclick="addNote()">&#128221; Add Note</button>
  <button onclick="clearAnns()" class="danger">&#10005; Clear</button>
  <div class="sep"></div>
  <button class="primary" onclick="exportPNG()">&#128190; PNG</button>
  <button onclick="exportSVG()">SVG</button>
  <span id="cursorInfo"></span>
</div>

<div class="wave-container" id="waveContainer">
  <div class="wave-inner">
    <svg id="waveSvg"></svg>
  </div>
</div>

<div id="annPanel"><div class="ann-empty">Click waveform to place cursor, then add notes</div></div>

<div class="footer">Click waveform | Drag cursor | Add notes (shown below) | Export PNG/SVG</div>
<script>{JS_CODE}</script>
</body></html>"""

    return html
