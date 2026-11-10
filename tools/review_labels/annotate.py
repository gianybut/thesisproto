"""Multi-user annotation site (deploy_annotation_site.md §3). One server on Gian's desktop, shared
through a Cloudflare tunnel; everyone works on the same labels.db.

    set ANNOTATE_PASSCODE=...   (or put it in .env at the repo root)
    python tools/review_labels/annotate.py [--port 8771]          # binds 127.0.0.1 only

Every route except /login and /api/login needs a signed session cookie (name + passcode), images
included. Frames come from the queue in annotate_db.py (test groups are never in it). A labelled
frame's boxes are stored as source='human'; the model's drafts are source='model'.

Also runs the backup job: every 30 min labels.db -> backups/labels_<timestamp>.db via the SQLite
backup API, and to GDRIVE_BACKUP_DIR if that folder exists.

The single-reviewer tool (server.py, port 8770) is unchanged; its 1,066 reviewed frames are not in
this queue. Do not use it for train/val frames while this site runs.
"""

import argparse
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import sys
import threading
import time
from datetime import datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import annotate_db as adb  # noqa: E402

HERE = Path(__file__).resolve().parent
USERS = ['Gian', 'Janmikael', 'Kyle']
SESSION_S = 7 * 24 * 3600
CACHE = adb.ANN / 'cache'
BACKUPS = adb.ROOT / 'backups'
OLD_COUNTS_MD = adb.ROOT / 'results' / 'local_datasets_nz.md'


def load_env():
    p = adb.ROOT / '.env'
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
PASSCODE = os.environ.get('ANNOTATE_PASSCODE', '')
_key_file = adb.ANN / '.session_key'
if not _key_file.exists():
    _key_file.parent.mkdir(parents=True, exist_ok=True)
    _key_file.write_text(secrets.token_hex(32))
KEY = (_key_file.read_text().strip() + PASSCODE).encode()   # changing the passcode logs everyone out
_fails = {}


def sign(user, exp):
    msg = f'{user}|{exp}'
    return msg + '|' + hmac.new(KEY, msg.encode(), hashlib.sha256).hexdigest()


def check(token):
    try:
        user, exp, mac = token.split('|')
    except (AttributeError, ValueError):
        return None
    good = hmac.new(KEY, f'{user}|{exp}'.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(mac, good) and float(exp) > time.time() and user in USERS:
        return user
    return None


def resized(fid):
    """JPEG, longest side <= 1280, quality 85, cached on first request."""
    out = CACHE / fid
    if not out.exists():
        from PIL import Image
        CACHE.mkdir(parents=True, exist_ok=True)
        im = Image.open(adb.FRAMES_DIR / fid).convert('RGB')
        im.thumbnail((1280, 1280))
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=85)
        tmp = out.with_suffix('.tmp')
        tmp.write_bytes(buf.getvalue())
        tmp.replace(out)
    return out.read_bytes()


def old_counts():
    rows = {}
    if OLD_COUNTS_MD.exists():
        for line in OLD_COUNTS_MD.read_text(encoding='utf-8').splitlines():
            p = [x.strip() for x in line.strip('|').split('|')]
            if len(p) == 7 and p[0] in ('train', 'val', 'test') and p[0] not in rows and p[1].isdigit():
                rows[p[0]] = dict(frames=int(p[1]), negatives=int(p[2]), **dict(zip(adb.CODES, map(int, p[3:]))))
    return rows


def stats(c):
    now = time.time()
    per_user = {u: dict(labeled=0, skipped=0, last_hour=0) for u in USERS}
    for u, st, n in c.execute("SELECT labeled_by, status, COUNT(*) FROM frames WHERE status IN ('labeled','skipped') "
                              "GROUP BY labeled_by, status"):
        per_user.setdefault(u, dict(labeled=0, skipped=0, last_hour=0))[st] = n
    for u, n in c.execute("SELECT user, COUNT(*) FROM events WHERE action IN ('labeled','skipped') AND timestamp > ? "
                          "GROUP BY user", (now - 3600,)):
        per_user.setdefault(u, dict(labeled=0, skipped=0, last_hour=0))['last_hour'] = n
    first = c.execute("SELECT MIN(timestamp) FROM events WHERE action IN ('labeled','skipped')").fetchone()[0]
    total = c.execute("SELECT COUNT(*) FROM frames WHERE status IN ('labeled','skipped')").fetchone()[0]
    remaining = {}
    for t, s, n in c.execute("SELECT COALESCE(tier,'no draft yet'), split, COUNT(*) FROM frames "
                             "WHERE status IN ('todo','in_progress') GROUP BY 1, 2"):
        remaining.setdefault(t, {})[s] = n
    new = {s: dict(frames=0, negatives=0, **{k: 0 for k in adb.CODES}) for s in ('train', 'val')}
    for s, n in c.execute("SELECT split, COUNT(*) FROM frames WHERE status='labeled' GROUP BY split"):
        new[s]['frames'] = n
    for s, n in c.execute("SELECT f.split, COUNT(*) FROM frames f WHERE status='labeled' AND NOT EXISTS "
                          "(SELECT 1 FROM boxes b WHERE b.frame_id=f.frame_id) GROUP BY f.split"):
        new[s]['negatives'] = n
    for s, k, n in c.execute("SELECT f.split, b.class_id, COUNT(*) FROM boxes b JOIN frames f USING(frame_id) "
                             "WHERE f.status='labeled' AND b.source='human' GROUP BY 1, 2"):
        new[s][adb.CODES[k]] = n
    open_now = [dict(r) for r in c.execute("SELECT frame_id, locked_by, lock_expires FROM frames "
                                           "WHERE status='in_progress' AND lock_expires > ?", (now,))]
    return dict(per_user=per_user, remaining=remaining, new=new, old=old_counts(), open=open_now, total_done=total,
                per_hour_overall=round(total / max((now - first) / 3600, 1 / 60), 1) if first else 0)


def with_prefetch(c, f):
    """Attach the next few queued frame ids so the browser can load their images in the background."""
    if not f:
        return {'done': True}
    f['prefetch'] = [r[0] for r in c.execute("SELECT frame_id FROM frames WHERE status='todo' "
                                             "ORDER BY priority, rnd LIMIT 3")]
    return f


def backup_once(tag=''):
    BACKUPS.mkdir(exist_ok=True)
    name = f'labels_{datetime.now():%Y%m%d_%H%M%S}{tag}.db'
    src = sqlite3.connect(adb.DB_PATH)
    try:
        for dest_dir in [BACKUPS] + ([Path(os.environ['GDRIVE_BACKUP_DIR'])]
                                     if os.environ.get('GDRIVE_BACKUP_DIR') and Path(os.environ['GDRIVE_BACKUP_DIR']).is_dir() else []):
            dst = sqlite3.connect(dest_dir / name)
            with dst:
                src.backup(dst)
            dst.close()
    finally:
        src.close()
    return BACKUPS / name


def backup_loop():
    while True:
        time.sleep(1800)
        try:
            print('backup:', backup_once(), flush=True)
        except Exception as e:   # a failed backup must never stop the site
            print('backup failed:', e, flush=True)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def send(self, code, body, ctype='application/json', headers=()):
        data = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'private, max-age=86400' if ctype == 'image/jpeg' else 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def user(self):
        ck = SimpleCookie(self.headers.get('Cookie', ''))
        return check(ck['ann'].value) if 'ann' in ck else None

    def body(self):
        n = int(self.headers.get('Content-Length', 0))
        if n > 1_000_000:
            raise ValueError('too large')
        return json.loads(self.rfile.read(n) or b'{}')

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/login':
            return self.send(200, (HERE / 'annotate_login.html').read_bytes(), 'text/html; charset=utf-8')
        user = self.user()
        if not user:
            if u.path.startswith('/api/') or u.path.startswith('/img/'):
                return self.send(401, {'error': 'sign in again'})
            return self.send(302, b'', 'text/plain', [('Location', '/login')])
        c = adb.connect()
        try:
            if u.path in ('/', '/index.html'):
                return self.send(200, (HERE / 'annotate.html').read_bytes(), 'text/html; charset=utf-8')
            if u.path == '/stats':
                return self.send(200, (HERE / 'annotate_stats.html').read_bytes(), 'text/html; charset=utf-8')
            if u.path == '/api/me':
                return self.send(200, dict(user=user, history=adb.history(c, user)))
            if u.path == '/api/stats':
                return self.send(200, stats(c))
            if u.path == '/api/next':
                return self.send(200, with_prefetch(c, adb.next_frame(c, user)))
            if u.path.startswith('/img/'):
                fid = u.path[5:]
                if c.execute('SELECT 1 FROM frames WHERE frame_id=?', (fid,)).fetchone() is None:
                    return self.send(404, {'error': 'unknown frame'})   # only queued frames, never a path
                return self.send(200, resized(fid), 'image/jpeg')
            return self.send(404, {'error': 'not found'})
        finally:
            c.close()

    def do_POST(self):
        u = urlparse(self.path)
        try:
            p = self.body()
        except ValueError as e:
            return self.send(400, {'error': str(e)})
        if u.path == '/api/login':
            ip = self.headers.get('CF-Connecting-IP') or self.client_address[0]
            if _fails.get(ip, 0) >= 10:
                time.sleep(2)
            if not PASSCODE or p.get('user') not in USERS or not hmac.compare_digest(str(p.get('passcode', '')), PASSCODE):
                _fails[ip] = _fails.get(ip, 0) + 1
                return self.send(403, {'error': 'wrong name or passcode'})
            _fails.pop(ip, None)
            secure = '; Secure' if self.headers.get('X-Forwarded-Proto') == 'https' else ''
            ck = f'ann={sign(p["user"], int(time.time() + SESSION_S))}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_S}{secure}'
            return self.send(200, {'ok': True}, headers=[('Set-Cookie', ck)])
        if u.path == '/api/logout':
            return self.send(200, {'ok': True}, headers=[('Set-Cookie', 'ann=; Path=/; Max-Age=0')])
        user = self.user()
        if not user:
            return self.send(401, {'error': 'sign in again'})
        c = adb.connect()
        try:
            if u.path == '/api/heartbeat':
                return self.send(200, {'ok': adb.heartbeat(c, user, p.get('frame_id'))})
            if u.path == '/api/open':
                return self.send(200, adb.open_frame(c, user, p.get('frame_id')))
            if u.path == '/api/save':
                adb.save(c, user, p['frame_id'], p['version'], p.get('boxes', []), p.get('action', 'labeled'))
                return self.send(200, with_prefetch(c, adb.next_frame(c, user)))
            return self.send(404, {'error': 'not found'})
        except LookupError as e:
            return self.send(409, {'error': str(e), 'frame': adb.frame_payload(c, p.get('frame_id'))})
        except PermissionError as e:
            return self.send(423, {'error': str(e)})
        except (ValueError, KeyError, TypeError) as e:
            return self.send(400, {'error': str(e)})
        finally:
            c.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8771)
    ap.add_argument('--no-backup', action='store_true')
    a = ap.parse_args()
    if len(PASSCODE) < 8:
        sys.exit('Set ANNOTATE_PASSCODE (8+ characters) in the environment or in .env at the repo root.')
    adb.connect().close()
    if not a.no_backup:
        print('backup:', backup_once('_start'), flush=True)
        threading.Thread(target=backup_loop, daemon=True).start()
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    srv.daemon_threads = True
    print(f'Annotation site: http://127.0.0.1:{a.port}  (database {adb.DB_PATH})', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    sys.exit(main())
