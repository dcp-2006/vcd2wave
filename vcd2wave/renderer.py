"""HTML waveform renderer with scroll, zoom, and improved display."""


def gen_html(signals, max_time, title="Waveform"):
    """Generate an HTML page visualizing the parsed VCD signals."""

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
        sig_data.append({
            'name': disp_name,
            'width': w,
            'trans': trans
        })

    import json
    sig_json = json.dumps(sig_data)
    num_sigs = len(sig_data)
    svg_height = num_sigs * ROW_H + 30

    JS_CODE = """
const sigData = SIG_DATA_PLACEHOLDER;
const maxTime = MAX_TIME_PLACEHOLDER;
const ROW_H = ROW_H_PLACEHOLDER;
const LABEL_W = LABEL_W_PLACEHOLDER;
let zoom = 100;

function draw() {
  var svg = document.getElementById('waveSvg');
  var baseW = maxTime * 0.002;
  var w = baseW * zoom / 100;
  svg.setAttribute('width', Math.max(w + 100, 800));
  svg.setAttribute('viewBox', '0 0 ' + Math.max(w + 100, 800) + ' ' + (ROW_H * sigData.length + 30));

  var html = '';
  var gridStep = 1;
  if (maxTime > 1000) gridStep = 10;
  if (maxTime > 10000) gridStep = 100;
  if (maxTime > 100000) gridStep = 1000;
  if (maxTime > 1000000) gridStep = 10000;
  var ppPs = w / maxTime;

  // Grid lines
  for (var t = 0; t <= maxTime; t += gridStep) {
    var x = t * ppPs;
    html += '<line x1="' + x + '" y1="0" x2="' + x + '" y2="' + ROW_H * sigData.length + '" stroke="#f0f0f0" stroke-width="1"/>';
    var dt = t, unit = 'ps';
    if (dt >= 1000) { dt = dt/1000; unit = 'ns'; }
    if (dt >= 1000) { dt = dt/1000; unit = 'us'; }
    if (dt >= 1000) { dt = dt/1000; unit = 'ms'; }
    html += '<text x="' + (x+3) + '" y="14" font-size="10" fill="#95a5a6">' + dt.toFixed(dt<10?1:0) + unit + '</text>';
  }

  // Signals
  for (var i = 0; i < sigData.length; i++) {
    var sig = sigData[i];
    var y0 = i * ROW_H;
    var isBus = sig.width > 1;
    html += '<rect x="0" y="' + y0 + '" width="100%" height="' + ROW_H + '" fill="' + (i%2===0?'#fff':'#fafafa') + '"/>';

    // Label
    var labelColor = isBus ? '#2980b9' : '#2c3e50';
    html += '<text x="5" y="' + (y0 + ROW_H/2 + 5) + '" font-size="12" font-weight="600" fill="' + labelColor + '">' + sig.name + '</text>';

    var trans = sig.trans;
    if (!trans || trans.length === 0) continue;
    var prevT = trans[0][0];
    var prevV = trans[0][1];

    for (var j = 0; j < trans.length; j++) {
      var t = trans[j][0];
      var v = trans[j][1];
      var x1 = prevT * ppPs + LABEL_W;
      var x2 = t * ppPs + LABEL_W;

      if (isBus) {
        html += '<rect x="' + x1 + '" y="' + (y0+4) + '" width="' + Math.max(4, x2-x1) + '" height="' + (ROW_H-8) + '" fill="#d5f4e6" stroke="#27ae60" stroke-width="0.5" rx="2"/>';
        if (x2 - x1 > 25) {
          html += '<text x="' + (x1+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="11" font-family="Consolas,monospace" fill="#1a7a4a">' + prevV + '</text>';
        }
      } else {
        var lvl = y0 + (prevV==='1'?8:ROW_H-8);
        html += '<line x1="' + x1 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + lvl + '" stroke="#2c3e50" stroke-width="1.5"/>';
        if (v !== prevV) {
          var nl = y0 + (v==='1'?8:ROW_H-8);
          html += '<line x1="' + x2 + '" y1="' + lvl + '" x2="' + x2 + '" y2="' + nl + '" stroke="#2c3e50" stroke-width="1.5"/>';
        }
      }
      prevT = t;
      prevV = v;
    }

    // Draw to end
    var xEnd = maxTime * ppPs + LABEL_W;
    if (isBus) {
      html += '<rect x="' + (prevT*ppPs+LABEL_W) + '" y="' + (y0+4) + '" width="' + Math.max(4, xEnd-prevT*ppPs-LABEL_W) + '" height="' + (ROW_H-8) + '" fill="#d5f4e6" stroke="#27ae60" stroke-width="0.5" rx="2"/>';
      if (xEnd - prevT*ppPs - LABEL_W > 25) {
        html += '<text x="' + (prevT*ppPs+LABEL_W+4) + '" y="' + (y0+ROW_H/2+4) + '" font-size="11" font-family="Consolas,monospace" fill="#1a7a4a">' + prevV + '</text>';
      }
    } else {
      var lvl = y0 + (prevV==='1'?8:ROW_H-8);
      html += '<line x1="' + (prevT*ppPs+LABEL_W) + '" y1="' + lvl + '" x2="' + xEnd + '" y2="' + lvl + '" stroke="#2c3e50" stroke-width="1.5"/>';
    }
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

// Mouse drag scroll
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
body {{font-family:'Segoe UI','Consolas',monospace;background:#fafafa}}
.toolbar {{position:sticky;top:0;z-index:100;background:#fff;border-bottom:2px solid #2980b9;
  padding:8px 16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.toolbar .title {{font-size:16px;font-weight:bold;color:#2c3e50;margin-right:20px}}
.toolbar .info {{font-size:12px;color:#7f8c8d;margin-right:auto}}
.toolbar button {{padding:6px 14px;border:1px solid #bdc3c7;border-radius:4px;background:#fff;
  cursor:pointer;font-size:13px;color:#2c3e50;user-select:none}}
.toolbar button:hover {{background:#ecf0f1;border-color:#2980b9}}
.toolbar input[type=range] {{width:180px;vertical-align:middle}}
.zoom-label {{font-size:12px;color:#7f8c8d;min-width:40px;text-align:center}}
.wave-container {{overflow-x:auto;overflow-y:hidden;cursor:grab;background:#fff;border-top:1px solid #ddd}}
.wave-container:active {{cursor:grabbing}}
.wave-inner {{position:relative}}
.wave-inner svg {{display:block}}
.footer {{text-align:center;padding:8px;font-size:11px;color:#95a5a6;border-top:1px solid #eee}}
.status-bar {{position:sticky;bottom:0;z-index:100;background:#fff;border-top:1px solid #ddd;
  padding:4px 16px;font-size:11px;color:#7f8c8d;display:flex;gap:16px}}
</style>
</head><body>

<div class="toolbar">
  <span class="title">{title}</span>
  <span class="info">{num_sigs} signals | {max_time} ps</span>
  <button onclick="zoomIn()">[+] Zoom In</button>
  <span class="zoom-label" id="zoomLabel">100%</span>
  <button onclick="zoomOut()">[-] Zoom Out</button>
  <button onclick="zoomReset()">Reset</button>
  <input type="range" id="zoomSlider" min="10" max="500" value="100" oninput="zoomSet(this.value)">
  <span style="color:#95a5a6;margin:0 4px">|</span>
  <button onclick="scrollLeft()">&lt; Left</button>
  <button onclick="scrollRight()">Right &gt;</button>
</div>

<div class="wave-container" id="waveContainer">
  <div class="wave-inner">
    <svg id="waveSvg" height="{svg_height}"></svg>
  </div>
</div>

<div class="status-bar">
  <span>Drag to scroll | Use zoom buttons to resize</span>
</div>

<script>{JS_CODE}</script>
<div class="footer">vcd2wave - waveform visualizer</div>
</body></html>"""

    return html
