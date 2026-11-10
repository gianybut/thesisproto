"""Count check for the near-zone local YOLO dataset (data/local/yolo_nz by default).

Counts frames, no-damage frames and boxes per class per split from the label files, compares them
with the first table in results/local_datasets_nz.md, and prints a SHA-256 over the sorted test
file list plus test label contents (to prove the test set did not change).

    python ml/local/check_counts.py                      # compare with the md table
    python ml/local/check_counts.py --expect-test-hash H # also require this test hash
    python ml/local/check_counts.py --no-compare         # just print (after a new export)

Exit code 1 on any mismatch.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = ['D00', 'D10', 'D20', 'D40']
SPLITS = ['train', 'val', 'test']


def count(ds):
    out = {}
    for s in SPLITS:
        imgs = sorted((ds / 'images' / s).glob('*.jpg'))
        row = dict(frames=len(imgs), neg=0, **{n: 0 for n in NAMES})
        for im in imgs:
            lab = ds / 'labels' / s / (im.stem + '.txt')
            lines = [l for l in lab.read_text().splitlines() if l.strip()] if lab.exists() else []
            if not lines:
                row['neg'] += 1
            for l in lines:
                row[NAMES[int(l.split()[0])]] += 1
        out[s] = row
    return out


def test_hash(ds):
    h = hashlib.sha256()
    for im in sorted((ds / 'images' / 'test').glob('*.jpg')):
        lab = ds / 'labels' / 'test' / (im.stem + '.txt')
        h.update(im.name.encode() + b'\0' + (lab.read_bytes().replace(b'\r\n', b'\n') if lab.exists() else b'') + b'\0')
    return h.hexdigest()


def expected(md):
    rows = {}
    for line in md.read_text(encoding='utf-8').splitlines():
        m = re.match(r'\|\s*(train|val|test)\s*\|' + r'\s*(\d+)\s*\|' * 6, line)
        if m and m.group(1) not in rows:
            v = list(map(int, m.groups()[1:]))
            rows[m.group(1)] = dict(frames=v[0], neg=v[1], **dict(zip(NAMES, v[2:])))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dataset', default=str(ROOT / 'data/local/yolo_nz'))
    ap.add_argument('--md', default=str(ROOT / 'results/local_datasets_nz.md'))
    ap.add_argument('--expect-test-hash')
    ap.add_argument('--no-compare', action='store_true')
    a = ap.parse_args()
    ds = Path(a.dataset)
    got = count(ds)
    print('| Split | Frames | No damage | ' + ' | '.join(NAMES) + ' |')
    for s in SPLITS:
        r = got[s]
        print(f"| {s} | {r['frames']} | {r['neg']} | " + ' | '.join(str(r[n]) for n in NAMES) + ' |')
    tot_f = sum(r['frames'] for r in got.values())
    tot_b = sum(r[n] for r in got.values() for n in NAMES)
    th = test_hash(ds)
    print(f'total frames {tot_f}, boxes {tot_b}, test hash {th}')
    ok = True
    if not a.no_compare:
        exp = expected(Path(a.md))
        for s in SPLITS:
            if exp.get(s) != got[s]:
                ok = False
                print(f'MISMATCH {s}: expected {exp.get(s)} got {got[s]}')
    if a.expect_test_hash and a.expect_test_hash != th:
        ok = False
        print('MISMATCH test hash')
    print('OK' if ok else 'FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
