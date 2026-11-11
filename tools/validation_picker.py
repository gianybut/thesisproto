"""Choose the validation pictures by hand, in the browser (this PC only).

    python tools/validation_picker.py        then open http://127.0.0.1:5077

Shows every human-labelled damage of the train and val splits, one damage type at a time (test is
left out: its labels are frozen). Click a picture to choose it; PER_CLASS per type. The choice is
saved as you go in data/local/validation_sheet/selection.json. "Create Word file" draws the sheet
(ml/local/validation_sheet.py) and builds the two-page Word file (tools/make_validation_letter.js,
needs `npm install --prefix tools --no-save docx` once). The letter then says the researchers
selected the samples, not that they were drawn at random.
"""

import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
from flask import Flask, Response, abort, jsonify, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ml' / 'local'))
import validation_sheet as vs  # noqa: E402

PER_CLASS = 10
PORT = 5077
NAMES = {'D00': 'Longitudinal crack', 'D10': 'Transverse crack', 'D20': 'Alligator crack', 'D40': 'Pothole'}
SELECTION = vs.SHEET / 'selection.json'
DOCX = vs.SHEET / 'OcuLubak_dataset_validation.docx'

app = Flask(__name__)
POOL = vs.pool()
BY_ID = {b['id']: b for b in POOL}


def saved_selection():
    """The saved choice, else the random pick the sheet was last built from."""
    sel = {c: [] for c in vs.CODES}
    if SELECTION.exists():
        got = json.loads(SELECTION.read_text(encoding='utf-8'))
    else:
        got = {}
        items = vs.SHEET / 'items.csv'
        if items.exists():
            for r in _rows(items):
                got.setdefault(r['class'], []).append(r.get('id'))
    for c in vs.CODES:
        sel[c] = [i for i in got.get(c, []) if i in BY_ID and vs.CODES[BY_ID[i]['cls']] == c][:PER_CLASS]
    return sel


def _rows(path):
    import csv
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def clean(sel):
    out = {}
    for c in vs.CODES:
        ids = []
        for i in sel.get(c, []):
            if i in BY_ID and vs.CODES[BY_ID[i]['cls']] == c and i not in ids:
                ids.append(i)
        out[c] = ids[:PER_CLASS]
    return out


@app.get('/')
def index():
    return Response(PAGE, mimetype='text/html')


@app.get('/api/state')
def state():
    rng = random.Random(vs.SEED)
    classes = {}
    for ci, code in enumerate(vs.CODES):
        ids = [b['id'] for b in POOL if b['cls'] == ci]
        rng.shuffle(ids)
        classes[code] = ids
    return jsonify(classes=classes, names=NAMES, per_class=PER_CLASS, selection=saved_selection(),
                   docx=str(DOCX) if DOCX.exists() else None)


@app.get('/tile/<split>/<stem>/<int:line>.jpg')
def tile(split, stem, line):
    b = BY_ID.get(f'{split}/{stem}/{line}')
    if not b:
        abort(404)
    ok, buf = cv2.imencode('.jpg', vs.tile(b), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return Response(buf.tobytes(), mimetype='image/jpeg', headers={'Cache-Control': 'max-age=86400'})


@app.post('/api/selection')
def save():
    sel = clean(request.get_json(force=True))
    vs.SHEET.mkdir(parents=True, exist_ok=True)
    SELECTION.write_text(json.dumps(sel, indent=1), encoding='utf-8')
    return jsonify(ok=True)


@app.post('/api/build')
def build():
    sel = clean(request.get_json(force=True))
    short = [f'{c} {NAMES[c]}' for c in vs.CODES if len(sel[c]) != PER_CLASS]
    if short:
        return jsonify(ok=False, error=f'Choose {PER_CLASS} pictures for: ' + ', '.join(short) + '.'), 400
    SELECTION.write_text(json.dumps(sel, indent=1), encoding='utf-8')
    node = shutil.which('node')
    if not node:
        return jsonify(ok=False, error='Node.js was not found, so the Word file could not be built.'), 500
    try:
        with open(DOCX, 'ab'):
            pass
    except PermissionError:
        return jsonify(ok=False, error='The Word file is open. Close it in Word, then create it again.'), 409
    vs.build({c: [BY_ID[i] for i in sel[c]] for c in vs.CODES}, 'by_hand')
    r = subprocess.run([node, str(ROOT / 'tools' / 'make_validation_letter.js')], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        return jsonify(ok=False, error='The Word file could not be built: ' + (r.stderr or r.stdout).strip()[-300:]), 500
    return jsonify(ok=True, docx=str(DOCX))


@app.post('/api/open')
def open_docx():
    if not DOCX.exists():
        return jsonify(ok=False, error='Create the Word file first.'), 404
    os.startfile(DOCX)  # Windows: opens it in Word
    return jsonify(ok=True)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Choose validation pictures</title>
<style>
:root { --blue:#3B6FA8; --ink:#1B2430; --muted:#5A6675; --line:#D8DEE6; --page:#F6F8FB; --ok:#2E7D4F; --err:#B3261E; }
* { box-sizing:border-box; }
body { margin:0; font:16px/1.45 "Public Sans", system-ui, "Segoe UI", sans-serif; color:var(--ink); background:var(--page); }
header { position:sticky; top:0; z-index:5; background:#fff; border-bottom:1px solid var(--line); padding:12px 24px; }
.top { display:flex; gap:16px; align-items:center; flex-wrap:wrap; }
h1 { font-size:20px; margin:0; } .sub { color:var(--muted); font-size:14px; margin:2px 0 0; }
.grow { flex:1; min-width:240px; }
button { font:inherit; cursor:pointer; border-radius:6px; padding:8px 14px; border:1px solid var(--line); background:#fff; color:var(--ink); }
button.primary { background:var(--blue); border-color:var(--blue); color:#fff; font-weight:600; }
button:disabled { opacity:.5; cursor:not-allowed; }
button.link { border:0; background:none; color:var(--blue); padding:0; text-decoration:underline; }
.tabs { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
.tab { border-radius:6px 6px 0 0; border-bottom:3px solid transparent; }
.tab[aria-selected=true] { border-bottom-color:var(--blue); font-weight:600; }
.tab .n { font-variant-numeric:tabular-nums; color:var(--muted); font-weight:400; }
.tab .done { color:var(--ok); font-weight:600; }
main { padding:16px 24px 48px; max-width:1500px; margin:0 auto; }
h2 { font-size:16px; margin:20px 0 8px; display:flex; gap:12px; align-items:baseline; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:10px; }
.chosen { grid-template-columns:repeat(5,minmax(0,1fr)); }
.t { position:relative; padding:0; border:3px solid transparent; border-radius:6px; background:#fff; overflow:hidden; text-align:left;
     box-shadow:0 1px 2px rgba(27,36,48,.12); }
.t img { display:block; width:100%; aspect-ratio:600/380; background:#E9EDF2; }
.t .cap { display:block; font-size:12px; color:var(--muted); padding:3px 6px; font-variant-numeric:tabular-nums; }
.t.on { border-color:var(--blue); }
.t .badge { position:absolute; top:6px; left:6px; background:var(--blue); color:#fff; font-weight:700; font-size:13px; border-radius:4px; padding:1px 7px; }
.empty { border:1px dashed var(--line); border-radius:6px; color:var(--muted); padding:18px; background:#fff; }
.notice { margin-top:10px; padding:10px 14px; border-radius:6px; border:1px solid var(--line); background:#fff; display:none; }
.notice.ok { display:block; border-color:var(--ok); } .notice.err { display:block; border-color:var(--err); }
.notice b { margin-right:6px; }
.more { margin:16px 0; }
</style></head><body>
<header>
  <div class="top">
    <div class="grow"><h1>Choose the validation pictures</h1>
      <p class="sub" id="sub"></p></div>
    <span id="total" class="sub"></span>
    <button id="open" hidden>Open in Word</button>
    <button id="build" class="primary" disabled>Create Word file</button>
  </div>
  <div id="notice" class="notice" role="status"></div>
  <div class="tabs" id="tabs" role="tablist"></div>
</header>
<main>
  <h2><span id="chosenTitle"></span><button class="link" id="clear">Remove all of this type</button></h2>
  <div id="chosen" class="grid chosen"></div>
  <h2 id="allTitle"></h2>
  <div id="all" class="grid"></div>
  <div class="more"><button id="more">Show more pictures</button></div>
</main>
<script>
const PAGE = 48;
let S, cur = 'D00', shown = PAGE;
const $ = (id) => document.getElementById(id);
const src = (id) => '/tile/' + id + '.jpg';
const frame = (id) => id.split('/')[1];
function notice(kind, text) { const n = $('notice'); n.className = 'notice ' + (kind || ''); n.innerHTML = ''; if (!kind) return;
  const b = document.createElement('b'); b.textContent = kind === 'ok' ? '✓ Done:' : '! Problem:'; n.append(b, text); }
function count() { return Object.values(S.selection).reduce((a, v) => a + v.length, 0); }
function save() { fetch('/api/selection', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(S.selection) }); }
function toggle(id) {
  const sel = S.selection[cur], i = sel.indexOf(id);
  if (i >= 0) sel.splice(i, 1);
  else if (sel.length >= S.per_class) { notice('err', `You already have ${S.per_class} ${S.names[cur].toLowerCase()} pictures. Remove one first.`); return; }
  else sel.push(id);
  notice(); save(); render();
}
function tileEl(id, n) {
  const b = document.createElement('button'); b.className = 't' + (n ? ' on' : ''); b.type = 'button';
  b.setAttribute('aria-pressed', n ? 'true' : 'false');
  const img = document.createElement('img'); img.loading = 'lazy'; img.src = src(id); img.alt = S.names[cur] + ', ' + frame(id);
  const cap = document.createElement('span'); cap.className = 'cap'; cap.textContent = frame(id) + (n ? ' · chosen, click to remove' : '');
  b.append(img, cap);
  if (n) { const g = document.createElement('span'); g.className = 'badge'; g.textContent = n; b.append(g); }
  b.onclick = () => toggle(id); return b;
}
function render() {
  const codes = Object.keys(S.classes), total = S.per_class * codes.length;
  $('sub').textContent = `${S.per_class} for each damage type, ${total} in all. Click a picture to choose it, click it again to remove it.`;
  $('total').textContent = `${count()} of ${total} chosen`;
  $('build').disabled = count() !== total;
  $('tabs').innerHTML = '';
  codes.forEach((c) => { const t = document.createElement('button'); t.className = 'tab'; t.setAttribute('role', 'tab');
    t.setAttribute('aria-selected', c === cur); const n = S.selection[c].length;
    t.innerHTML = `${c} ${S.names[c]} <span class="${n === S.per_class ? 'done' : 'n'}">${n === S.per_class ? '✓ ' : ''}${n} of ${S.per_class}</span>`;
    t.onclick = () => { cur = c; shown = PAGE; notice(); render(); window.scrollTo(0, 0); }; $('tabs').append(t); });
  const sel = S.selection[cur], offset = codes.indexOf(cur) * S.per_class;
  $('chosenTitle').textContent = `Chosen ${S.names[cur].toLowerCase()} pictures (${sel.length} of ${S.per_class}), in sheet order`;
  $('clear').hidden = !sel.length;
  $('chosen').innerHTML = '';
  if (!sel.length) { const e = document.createElement('div'); e.className = 'empty'; e.style.gridColumn = '1 / -1';
    e.textContent = 'Nothing chosen yet. Pick from the pictures below.'; $('chosen').append(e); }
  sel.forEach((id, i) => $('chosen').append(tileEl(id, offset + i + 1)));
  const ids = S.classes[cur];
  $('allTitle').textContent = `All marked ${S.names[cur].toLowerCase()} pictures (${ids.length.toLocaleString()})`;
  $('all').innerHTML = '';
  ids.slice(0, shown).forEach((id) => { const i = sel.indexOf(id); $('all').append(tileEl(id, i >= 0 ? offset + i + 1 : 0)); });
  $('more').hidden = shown >= ids.length;
  $('more').textContent = `Show more pictures (${Math.min(shown, ids.length)} of ${ids.length.toLocaleString()} shown)`;
}
$('more').onclick = () => { shown += PAGE; render(); };
$('clear').onclick = () => { S.selection[cur] = []; save(); render(); };
$('build').onclick = async () => {
  $('build').disabled = true; $('build').textContent = 'Creating…';
  const r = await fetch('/api/build', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(S.selection) });
  const j = await r.json(); $('build').textContent = 'Create Word file'; render();
  if (j.ok) { notice('ok', 'Word file created at ' + j.docx); $('open').hidden = false; } else notice('err', j.error);
};
$('open').onclick = async () => { const j = await (await fetch('/api/open', { method:'POST' })).json(); if (!j.ok) notice('err', j.error); };
fetch('/api/state').then((r) => r.json()).then((j) => { S = j; $('open').hidden = !j.docx; render(); });
</script></body></html>
"""

if __name__ == '__main__':
    print(f'Choose the validation pictures at http://127.0.0.1:{PORT}  (Ctrl+C to stop)')
    app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)
