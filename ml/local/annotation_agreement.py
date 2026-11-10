"""Step 7.3: agreement between the expert's answers and the reviewed labels.

    python ml/local/annotation_agreement.py [--responses data/local/annotation_form/responses.csv]

Reads the Google Form responses (CSV downloaded from the response sheet: one row per respondent,
one column per box, titled "<ID>: what is inside the magenta box?") and answer_key.csv. Reports
percent agreement and Cohen's kappa overall (5 categories: D00, D10, D20, D40, not damage), and per
class (one class against the rest, so a per-class kappa is defined), plus a confusion matrix and
the list of boxes the expert labelled differently (candidates for label correction in val/test;
after corrections, only the final test evaluation is re-run).
Writes results/step7_expert_agreement.md and data/local/annotation_form/disagreements.csv.
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from common import OUT, ROOT, read_csv, write_csv

CATS = ['D00', 'D10', 'D20', 'D40', 'NOT']


def kappa(a, b, cats):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in cats) / n ** 2
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po


def answer_code(text):
    t = (text or '').strip()
    return 'NOT' if t.lower().startswith('not') else t[:3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--responses', default=str(OUT / 'annotation_form' / 'responses.csv'))
    a = ap.parse_args()
    key = {k['id']: k for k in read_csv(OUT / 'annotation_form' / 'answer_key.csv')}
    with open(a.responses, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    head, data = rows[0], rows[1:]
    cols = {m.group(1): i for i, h in enumerate(head) if (m := re.match(r'(B\d{3}):', h))}
    name_col = next((i for i, h in enumerate(head) if h.strip().lower() == 'your name'), None)
    md = ['# Expert check of the reviewed labels', '']
    dis = []
    for row in data:
        who = row[name_col] if name_col is not None else 'respondent'
        ids = [i for i in sorted(key) if i in cols and row[cols[i]].strip()]
        ref = [key[i]['reviewed_class'] for i in ids]
        exp = [answer_code(row[cols[i]]) for i in ids]
        k, po = kappa(ref, exp, CATS)
        md += [f'## {who}: {len(ids)} boxes answered', '',
               f'Overall: agreement {po:.1%}, Cohen\'s kappa {k:.2f} (categories D00, D10, D20, D40, not damage).', '',
               '| Reviewed class | Boxes | Expert agrees | Agreement | Kappa (class vs rest) |', '|---|---|---|---|---|']
        for c in CATS[:4]:
            n = sum(r == c for r in ref)
            if not n:
                continue
            agree = sum(r == c and e == c for r, e in zip(ref, exp))
            kc, _ = kappa([r == c for r in ref], [e == c for e in exp], [True, False])
            md.append(f'| {c} | {n} | {agree} | {agree / n:.0%} | {kc:.2f} |')
        md += ['', 'Confusion (rows: reviewed label; columns: expert):', '',
               '| | ' + ' | '.join(CATS) + ' |', '|---|' + '---|' * len(CATS)]
        for c in CATS[:4]:
            md.append(f'| {c} | ' + ' | '.join(str(sum(r == c and e == d for r, e in zip(ref, exp))) for d in CATS) + ' |')
        md.append('')
        for i, r, e in zip(ids, ref, exp):
            if r != e:
                dis.append(dict(respondent=who, id=i, reviewed=r, expert=e, frame=key[i]['frame'],
                                split=key[i]['split'], x1=key[i]['x1'], y1=key[i]['y1'], x2=key[i]['x2'], y2=key[i]['y2']))
    md.append(f'{len(dis)} disagreements listed in data/local/annotation_form/disagreements.csv.')
    write_csv(OUT / 'annotation_form' / 'disagreements.csv', dis or [dict(respondent='', id='')])
    (ROOT / 'results' / 'step7_expert_agreement.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
