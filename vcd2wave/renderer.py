"""HTML waveform renderer with annotations, export, and themes."""


def gen_html(signals, max_time, title="Waveform"):
    filtered = {}
    for code, sig in signals.items():
        name = sig["name"]
        if "." not in name:
            filtered[code] = sig
    if len(filtered) < 5:
        filtered = signals

    ROW_H = 40
    LABEL_W = 160

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
let dragStartX = null, dragStartTime = null;

function ppPs() { return (maxTime * 0.002 * zoom / 100) / maxTime; }

function draw() {
  var svg = document.getElementById('waveSvg');
  var baseW = maxTime * 0.002;
  var w = baseW * zoom / 100;
  var totalH = sigData.length * ROW_H;
  svg.setAttribute('width', Math.max(w + LABEL_W + 20, 900));
  svg.setAttribute('viewBox', '0 0 ' + Math.max(w + LABEL_W + 20, 900) + ' ' + (totalH + 40));
  var pp = ppPs();

  var bg = theme === 'dark' ? '#1a1a2e' : '#fafafa';
  var gridColor = theme === 'dark' ? '#2a2a4e' : '#f0f0f0';
  var textColor = theme === 'dark' ? '#e0e0e0' : '#2c3e50';
  var busFill = theme === 'dark' ? '#1a3a2e' : '#d5f4e6';
  var busStroke = theme === 'dark' ? '#2ecc71' : '#27ae60';
  var busText = theme === 'dark' ? '#2ecc71' : '#1a7a4a';

  document.body.style.background = bg;
  document.body.style.color = textColor;

  var html = '<rect width="100%" height="100%" fill="' + bg + '"/>';

  var gridStep = 1;
  if (maxTime > 1000) gridStep = 10;
  if (maxTime > 10000) gridStep = 100;
  if (maxTime > 100000) gridStep = 1000;
  if (maxTime > 1000000) gridStep = 10000;

  for (var t = 0; t <= maxTime; t += gridStep) {
    var x = t * pp + LABEL_W;
    html += '<line x1="' + x + '" y1="0" x2="' + x + '" y2="' + totalH + '" stroke="' + gridColor + '" stroke-width="1"/>';
    var dt = t, unit = 'ps';
    if (dt >= 1000) { dt = dt/1000; unit = 'ns'; }
    if (dt >= 1000) { dt = dt/1000; unit = 'us'; }
    if (dt >= 1000) { dt = dt/1000; unit = 'ms'; }
    html += '<text x="' + (x+3) + '" y="14" font-size="10" fill="' + textColor + '" opacity="0.5">' + dt.toFixed(dt<10?1:0) + unit + '</text>';
  }

  var markers = annotations.filter(function(a) { return a.type === 'marker'; });
  for (var m = 0; m < markers.length; m++) {
    var mx = markers[m].time * pp + LABEL_W;
    html += '<line x1="' + mx + '" y1="0" x2="' + mx + '" y2="' + totalH + '" stroke="#e74c3c" stroke-width="1.5" stroke-dasharray="6,3"/>';
    html += '<text x="' + (mx+3) + '" y="' + (totalH-5) + '" font-size="10" fill="#e74c3c">' + markers[m].label + '</text>';
  }

  for (var i = 0; i < sigData.length; i++) {
    var sig = sigData[i];
    var y0 = i * ROW_H;
    var isBus = sig.width > 1;
    var rowBg = i % 2 === 0 ? 'transparent' : (theme==='dark'?'rgba(255,255,255,0.03)':'rgba(0,0,0,0.02)');
    html += '<rect x="0" y="' + y0 + '" width="100%" height="' + ROW_H + '" fill="' + rowBg + '"/>';
    var labelColor = isBus ? '#3498db' : textColor;
    html += '<text x="8" y="' + (y0 + ROW_H/2 + 5) + '" font-size="12" font-weight="600" fill="' + labelColor + '">' + sig.name + '</text>';

    var trans = sig.trans;
    if (!trans || trans.length === 0) continue;
    var prevT = trans[0][0];
    var prevV = trans[0][1];

    for (var j = 0; j < trans.length; j++) {
      var t = trans[j][0];
      var v = trans[j][1];
      var x1 = prevT * pp + LABEL_W;
      var x2 = t * pp + LABEL_W;

      if (isBus) {
        html += '<rect x="' + x1 + '" y="' + (y0+4) + '" width="' + Math.max(4, x2-x1) + '" height="' + (ROW_H-8) + '" fill="' + busFill + '" stroke="' + busStroke + '" stroke-width="0.5" rx="2"/>';
        if (x2 - x1 > 25) {
          html += '<text x="' + (x1+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="11" font-family="Consolas,monospace" fill="' + busText + '">' + prevV + '</text>';
        }
      } else {
        var lvl = y0 + (prevV==='1'?8:ROW_H-8);
        html += '<line x1="' + x1 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + lvl + '" stroke="' + textColor + '" stroke-width="1.5"/>';
        if (v !== prevV) {
          var nl = y0 + (v==='1'?8:ROW_H-8);
          html += '<line x1="' + x2 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + nl + '" stroke="' + textColor + '" stroke-width="1.5"/>';
        }
      }
      prevT = t;
      prevV = v;
    }
    var xEnd = maxTime * pp + LABEL_W;
    if (isBus) {
      html += '<rect x="' + (prevT*pp+LABEL_W) + '" y="' + (y0+4) + '" width="' + Math.max(4, xEnd-prevT*pp-LABEL_W) + '" height="' + (ROW_H-8) + '" fill="' + busFill + '" stroke="' + busStroke + '" stroke-width="0.5" rx="2"/>';
      if (xEnd - prevT*pp - LABEL_W > 25) {
        html += '<text x="' + (prevT*pp+LABEL_W+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="11" font-family="Consolas,monospace" fill="' + busText + '">' + prevV + '</text>';
      }
    } else {
      var lvl = y0 + (prevV==='1'?8:ROW_H-8);
      html += '<line x1="' + (prevT*pp+LABEL_W) + '" y1="' + lvl + '" x2="' + xEnd + '" y2="' + lvl + '" stroke="' + textColor + '" stroke-width="1.5"/>';
    }
  }

  // Annotations (text labels)
  var notes = annotations.filter(function(a) { return a.type === 'note'; });
  for (var n = 0; n < notes.length; n++) {
    var nx = notes[n].time * pp + LABEL_W;
    var ny = notes[n].sigIdx * ROW_H;
    html += '<rect x="' + nx + '" y="' + (ny-18) + '" width="' + Math.min(200, notes[n].label.length*7+10) + '" height="18" rx="3" fill="#ffeaa7" stroke="#fdcb6e" stroke-width="1"/>';
    html += '<text x="' + (nx+4) + '" y="' + (ny-5) + '" font-size="10" fill="#2d3436">' + notes[n].label + '</text>';
  }

  svg.innerHTML = html;
}

function zoomIn() { zoom = Math.min(500, zoom*1.5); zoomUpdate(); }
function zoomOut() { zoom = Math.max(10, zoom/1.5); zoomUpdate(); }
function zoomReset() { zoom = 100; zoomUpdate(); }
function zoomSet(v) { zoom = parseInt(v); zoomUpdate(); }
function zoomUpdate() {
  document.getElementById('zoomSlider').value = zoom;
  document.getElementById('zoomLabel').textContent = zoom + '%';
  draw();
}
function scrollLeft() { document.getElementById('waveContainer').scrollLeft -= 200; }
function scrollRight() { document.getElementById('waveContainer').scrollLeft += 200; }

function toggleTheme() {
  theme = theme === 'dark' ? 'light' : 'dark';
  document.getElementById('themeBtn').textContent = theme === 'dark' ? '☀ Light' : '🌙 Dark';
  draw();
}

function addMarker() {
  var t = prompt('Enter time (ps) to mark:');
  if (t === null) return;
  t = parseInt(t);
  if (isNaN(t) || t < 0 || t > maxTime) { alert('Invalid time (0-' + maxTime + ')'); return; }
  var label = prompt('Label:') || 'M' + (++annId);
  annotations.push({type:'marker', time:t, label:label});
  draw();
}

function addNote() {
  var t = prompt('Enter time (ps) for annotation:');
  if (t === null) return;
  t = parseInt(t);
  if (isNaN(t) || t < 0 || t > maxTime) { alert('Invalid time'); return; }
  var text = prompt('Annotation text:');
  if (!text) return;
  annotations.push({type:'note', time:t, sigIdx:0, label:text});
  draw();
}

function exportPNG() {
  var svg = document.getElementById('waveSvg');
  var svgData = svg.outerHTML;
  var canvas = document.createElement('canvas');
  var rect = svg.getBoundingClientRect();
  var scale = 2;
  canvas.width = rect.width * scale || 1920;
  canvas.height = rect.height * scale || 1080;
  var ctx = canvas.getContext('2d');
  ctx.fillStyle = theme === 'dark' ? '#1a1a2e' : '#fafafa';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.scale(scale, scale);
  var img = new Image();
  var blob = new Blob([svgData], {type:'image/svg+xml;charset=utf-8'});
  var url = URL.createObjectURL(blob);
  img.onload = function() {
    ctx.drawImage(img, 0, 0);
    URL.revokeObjectURL(url);
    canvas.toBlob(function(b) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(b);
      a.download = 'waveform.png';
      a.click();
    }, 'image/png');
  };
  img.src = url;
}

function exportSVG() {
  var svg = document.getElementById('waveSvg');
  var s = new XMLSerializer().serializeToString(svg);
  var blob = new Blob([s], {type:'image/svg+xml;charset=utf-8'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'waveform.svg';
  a.click();
}

(function() {
  var c = document.getElementById('waveContainer');
  var down = false, sx, sl;
  c.onmousedown = function(e) { down = true; sx = e.pageX - c.offsetLeft; sl = c.scrollLeft; };
  c.onmouseleave = function() { down = false; };
  c.onmouseup = function() { down = false; };
  c.onmousemove = function(e) { if (!down) return; e.preventDefault(); c.scrollLeft = sl - (e.pageX - c.offsetLeft - sx) * 1.5; };
})();

draw();
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
body {{font-family:'Segoe UI','Consolas',monospace;background:#fafafa;color:#2c3e50;transition:all 0.3s}}
.toolbar {{position:sticky;top:0;z-index:100;background:#fff;border-bottom:2px solid #3498db;
  padding:6px 14px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;transition:all 0.3s}}
.toolbar .title {{font-size:15px;font-weight:bold;color:#2c3e50;margin-right:16px}}
.toolbar .info {{font-size:11px;color:#7f8c8d;margin-right:auto}}
.toolbar button {{padding:5px 10px;border:1px solid #bdc3c7;border-radius:4px;background:#fff;
  cursor:pointer;font-size:12px;color:#2c3e50;user-select:none;transition:all 0.2s}}
.toolbar button:hover {{background:#ecf0f1;border-color:#3498db}}
.toolbar button.primary {{background:#3498db;color:#fff;border-color:#3498db}}
.toolbar button.primary:hover {{background:#2980b9}}
.toolbar input[type=range] {{width:120px;vertical-align:middle}}
.zoom-label {{font-size:11px;color:#7f8c8d;min-width:34px;text-align:center}}
.separator {{width:1px;height:24px;background:#ddd;margin:0 4px}}
.wave-container {{overflow-x:auto;overflow-y:hidden;cursor:grab;border-top:1px solid #ddd}}
.wave-container:active {{cursor:grabbing}}
.wave-inner svg {{display:block}}
.footer {{text-align:center;padding:6px;font-size:10px;color:#95a5a6;border-top:1px solid #eee}}
</style>
</head><body>

<div class="toolbar" id="toolbar">
  <span class="title">{title}</span>
  <span class="info">{num_sigs} signals | {max_time} ps</span>
  <div class="separator"></div>
  <button onclick="zoomIn()">[ + ]</button>
  <span class="zoom-label" id="zoomLabel">100%</span>
  <button onclick="zoomOut()">[ - ]</button>
  <button onclick="zoomReset()">Reset</button>
  <input type="range" id="zoomSlider" min="10" max="500" value="100" oninput="zoomSet(this.value)">
  <div class="separator"></div>
  <button onclick="scrollLeft()">&lt;</button>
  <button onclick="scrollRight()">&gt;</button>
  <div class="separator"></div>
  <button id="themeBtn" onclick="toggleTheme()">&#127769; Dark</button>
  <button onclick="addMarker()">&#9872; Marker</button>
  <button onclick="addNote()">&#128221; Annotate</button>
  <button class="primary" onclick="exportPNG()">&#128190; PNG</button>
  <button onclick="exportSVG()">SVG</button>
</div>

<div class="wave-container" id="waveContainer">
  <div class="wave-inner">
    <svg id="waveSvg" height="{num_sigs * ROW_H + 30}"></svg>
  </div>
</div>

<div class="footer">vcd2wave &mdash; export to SVG/PNG | add markers and annotations</div>
<script>{JS_CODE}</script>
</body></html>"""

    return html
