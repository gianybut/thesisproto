"""User acceptance test (UAT) analysis for Chapter V, Section 5.6.

Reads the Google Forms CSV export of the evaluation questionnaire and computes, as defined in
Chapter III, Section 3.8 (Equations 26 to 28) and Table 4.4.5.2:

  * the weighted mean of each item, x = sum(f_i * w_i) / n            (Equation 26)
  * the weighted mean and sample standard deviation of each dimension and of all items together,
    taken over the respondents' scores (a respondent's score for a dimension is the mean of their
    answers to its items)                                               (Equation 27)
  * a one-tailed one-sample t-test of each mean against the criterion mean 3.41,
    t = (x - 3.41) / (s / sqrt(n)), df = n - 1, p = P(T > t)            (Equation 28)
  * the verbal interpretation of each mean (Table 4.4.5.2), and the decision rule: the hypothesis
    is supported if the overall weighted mean is at least 3.41 and significantly greater than
    3.41 at the 0.05 level.

Everything is computed twice when the validator is identified: with all respondents, and without the
annotation validator, Engr. Carlo Almanzor of the DPWH Cavite 2nd District Engineering Office, who checked
the labels and also works at the main respondent office (Sections 3.6, 4.4.1 and 5.6.7 promise both
versions). Identify him by his respondent ID with --validator-id (and --id-column if the ID column is not
named "Respondent ID" or "ID"), or by any other column with --exclude COLUMN=VALUE / COLUMN~REGEX.

The dimensions of the questionnaire are not fixed in the code: they come from a JSON file that
maps each dimension to the CSV column headers of its items, in the order they should be reported:

    {
      "Functionality": ["The system detects road damage in the uploaded video.", "..."],
      "Usability": ["..."]
    }

A header may also be given as a regular expression by prefixing it with "re:", for example
"re:^\\[Usability\\]" for the bracketed grid items Google Forms exports as "Question [Row]".

Answers may be the numbers 1 to 5 or the labels of Table 4.4.5.1 (Strongly Disagree, Disagree,
Neutral, Agree, Strongly Agree; case and surrounding spaces are ignored). Blank answers are
skipped. Any other answer stops the script, so a wrongly mapped column is not silently averaged.

Usage:
    python tools/uat_analysis.py responses.csv --items uat_items.json
    python tools/uat_analysis.py responses.csv --items uat_items.json \\
        --validator-id R07 --out results/uat_results.md
    python tools/uat_analysis.py responses.csv --items uat_items.json --id-column "Respondent code" --validator-id 7

--exclude takes COLUMN=VALUE (exact match after trimming, case-insensitive) or COLUMN~REGEX; --engineer is kept
as an older name for --exclude.
Only the standard library is used.
"""
import argparse
import csv
import json
import math
import re
import sys

CRITERION = 3.41
ALPHA = 0.05
LABELS = {'strongly disagree': 1, 'disagree': 2, 'neutral': 3, 'agree': 4, 'strongly agree': 5}
# Table 4.4.5.2, applied to the mean rounded to two decimals
SCALE = [(4.21, 'Strongly Agree / Excellent'), (3.41, 'Agree / Very Good'), (2.61, 'Neutral / Good'),
         (1.81, 'Disagree / Fair'), (1.00, 'Strongly Disagree / Poor')]


# ---------------------------------------------------------------- Student's t distribution
def _betacf(a, b, x):
    """Continued fraction for the regularized incomplete beta function (Numerical Recipes, 6.4)."""
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    raise RuntimeError('incomplete beta did not converge')


def betainc(a, b, x):
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbeta) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta) * _betacf(b, a, 1.0 - x) / b


def t_upper_tail(t, df):
    """P(T > t) for Student's t with df degrees of freedom."""
    tail = 0.5 * betainc(df / 2.0, 0.5, df / (df + t * t))
    return tail if t >= 0 else 1.0 - tail


# ---------------------------------------------------------------- statistics
def mean_sd(values):
    n = len(values)
    m = sum(values) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1)) if n > 1 else float('nan')
    return m, sd


def one_sample_t(values, mu0=CRITERION):
    """Returns n, mean, sd, t, df, one-tailed p (H1: mean > mu0)."""
    n = len(values)
    m, sd = mean_sd(values)
    if n < 2:
        return n, m, sd, float('nan'), n - 1, float('nan')
    if sd == 0:
        t = math.inf if m > mu0 else (-math.inf if m < mu0 else 0.0)
        p = 0.0 if m > mu0 else 1.0
        return n, m, sd, t, n - 1, p
    t = (m - mu0) / (sd / math.sqrt(n))
    return n, m, sd, t, n - 1, t_upper_tail(t, n - 1)


def interpret(m):
    r = round(m + 1e-12, 2)
    for low, label in SCALE:
        if r >= low:
            return label
    return 'below scale'


# ---------------------------------------------------------------- input
def parse_answer(raw, where):
    s = (raw or '').strip()
    if not s:
        return None
    if s.lower() in LABELS:
        return LABELS[s.lower()]
    m = re.match(r'^([1-5])(?:\.0+)?(?:\s*[-–:)]\s*.*)?$', s)  # "4", "4.0", "4 - Agree"; not "4.5"
    if m:
        return int(m.group(1))
    raise SystemExit(f'Unrecognised answer {raw!r} in {where}. Check the --items mapping.')


def resolve_columns(headers, items):
    dims = {}
    for dim, specs in items.items():
        cols = []
        for spec in specs:
            if spec.startswith('re:'):
                hit = [h for h in headers if re.search(spec[3:], h)]
            else:
                hit = [h for h in headers if h.strip() == spec.strip()]
            if not hit:
                raise SystemExit(f'Dimension {dim!r}: no CSV column matches {spec!r}')
            cols += [h for h in hit if h not in cols]
        dims[dim] = cols
    seen = {}
    for dim, cols in dims.items():
        for c in cols:
            if c in seen:
                raise SystemExit(f'Column {c!r} is mapped to both {seen[c]!r} and {dim!r}')
            seen[c] = dim
    return dims


VALIDATOR = 'Engr. Carlo Almanzor (annotation validator, DPWH Cavite 2nd District Engineering Office)'
ID_COLUMNS = ('Respondent ID', 'ID')


def validator_matcher(validator_id, id_column, headers):
    """Match the validator's row by respondent ID (exact, after trimming, case-insensitive)."""
    if validator_id is None:
        return None
    names = {h.strip().lower(): h for h in headers}
    if id_column:
        col = names.get(id_column.strip().lower())
        if col is None:
            raise SystemExit(f'--id-column: no CSV column {id_column!r}')
    else:
        col = next((names[c.lower()] for c in ID_COLUMNS if c.lower() in names), None)
        if col is None:
            raise SystemExit(f'--validator-id needs an ID column: none of {ID_COLUMNS} found; give --id-column')
    vid = str(validator_id).strip().lower()
    return lambda row: (row.get(col) or '').strip().lower() == vid


def engineer_matcher(spec, headers):
    if not spec:
        return None
    m = re.match(r'^(.*?)(=|~)(.*)$', spec)
    if not m:
        raise SystemExit('--exclude must be COLUMN=VALUE or COLUMN~REGEX')
    col, op, val = m.group(1).strip(), m.group(2), m.group(3).strip()
    if col not in [h.strip() for h in headers]:
        raise SystemExit(f'--exclude: no CSV column {col!r}')
    col = next(h for h in headers if h.strip() == col)
    if op == '=':
        return lambda row: (row.get(col) or '').strip().lower() == val.lower()
    rx = re.compile(val, re.I)
    return lambda row: bool(rx.search(row.get(col) or ''))


# ---------------------------------------------------------------- analysis and report
def analyse(rows, dims):
    """rows: list of dicts. Returns item stats, dimension tests and the overall test."""
    item_stats = []
    for dim, cols in dims.items():
        for c in cols:
            vals = [v for v in (parse_answer(r.get(c), f'column {c!r}') for r in rows) if v is not None]
            if not vals:
                item_stats.append((dim, c, [0] * 5, 0, float('nan'), float('nan')))
                continue
            freq = [vals.count(w) for w in range(1, 6)]
            n = len(vals)
            wm = sum(f * w for f, w in zip(freq, range(1, 6))) / n          # Equation 26
            _, sd = mean_sd(vals)
            item_stats.append((dim, c, freq, n, wm, sd))
    dim_tests = {}
    overall_scores = []
    for dim, cols in dims.items():
        scores = []
        for r in rows:
            vals = [v for v in (parse_answer(r.get(c), f'column {c!r}') for c in cols) if v is not None]
            if vals:
                scores.append(sum(vals) / len(vals))
        dim_tests[dim] = one_sample_t(scores) if scores else None
    for r in rows:
        vals = [v for v in (parse_answer(r.get(c), f'column {c!r}') for cols in dims.values() for c in cols) if v is not None]
        if vals:
            overall_scores.append(sum(vals) / len(vals))
    overall = one_sample_t(overall_scores) if overall_scores else None
    return item_stats, dim_tests, overall


def fmt(x, d=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return 'n/a'
    if isinstance(x, float) and math.isinf(x):
        return '∞' if x > 0 else '−∞'
    return f'{x:.{d}f}'


def fmt_p(p):
    if p is None or math.isnan(p):
        return 'n/a'
    return '< 0.001' if p < 0.001 else f'{p:.3f}'


def report(title, rows, dims):
    item_stats, dim_tests, overall = analyse(rows, dims)
    out = [f'## {title}', '', f'Respondents: {len(rows)}', '']
    out += ['### Items (Equation 26)', '',
            '| Dimension | Item | SA (5) | A (4) | N (3) | D (2) | SD (1) | n | Weighted mean | SD | Interpretation |',
            '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for dim, c, freq, n, wm, sd in item_stats:
        f = freq[::-1]
        out.append(f'| {dim} | {c} | ' + ' | '.join(str(v) for v in f) + f' | {n} | {fmt(wm)} | {fmt(sd)} | '
                   + (interpret(wm) if n else 'n/a') + ' |')
    out += ['', f'### Dimensions and overall: one-tailed one-sample t-test against {CRITERION} (Equations 27 and 28)', '',
            '| Dimension | n | Weighted mean | SD | t | df | p (one-tailed) | Significant at 0.05 | Interpretation |',
            '|---|---:|---:|---:|---:|---:|---:|---|---|']
    for dim, res in list(dim_tests.items()) + [('Overall', overall)]:
        if res is None:
            out.append(f'| {dim} | 0 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |')
            continue
        n, m, sd, t, df, p = res
        sig = 'n/a' if math.isnan(p) else ('yes' if p < ALPHA else 'no')
        name = f'**{dim}**' if dim == 'Overall' else dim
        out.append(f'| {name} | {n} | {fmt(m)} | {fmt(sd)} | {fmt(t, 3)} | {df} | {fmt_p(p)} | {sig} | {interpret(m)} |')
    out.append('')
    if overall is None or math.isnan(overall[5]):
        out.append('Decision: not enough responses for the t-test (at least two respondents are needed).')
    else:
        n, m, sd, t, df, p = overall
        ok = round(m, 2) >= CRITERION and p < ALPHA
        out.append(f'Decision: the overall weighted mean is {fmt(m)} '
                   f'({"at least" if round(m, 2) >= CRITERION else "below"} {CRITERION}), t({df}) = {fmt(t, 3)}, '
                   f'one-tailed p = {fmt_p(p)}. The hypothesis is {"supported" if ok else "not supported"}.')
    out.append('')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('csv', help='Google Forms responses exported as CSV')
    ap.add_argument('--items', required=True, help='JSON file mapping each dimension to its item columns')
    ap.add_argument('--validator-id', help="respondent ID of Engr. Carlo Almanzor, the annotation validator")
    ap.add_argument('--id-column', help='CSV column that holds the respondent ID (default: "Respondent ID" or "ID")')
    ap.add_argument('--exclude', '--engineer', dest='exclude',
                    help='COLUMN=VALUE or COLUMN~REGEX that identifies the validator, if there is no ID column')
    ap.add_argument('--out', help='also write the report to this Markdown file')
    a = ap.parse_args()

    with open(a.csv, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    items = json.load(open(a.items, encoding='utf-8'))
    dims = resolve_columns(headers, items)
    if a.validator_id is not None and a.exclude:
        raise SystemExit('give either --validator-id or --exclude, not both')
    is_eng = validator_matcher(a.validator_id, a.id_column, headers) or engineer_matcher(a.exclude, headers)
    how = f'--validator-id {a.validator_id!r}' if a.validator_id is not None else f'--exclude {a.exclude!r}'

    out = ['# User acceptance test results', '',
           f'Source: `{a.csv}`; items: `{a.items}`; criterion mean {CRITERION}; one-tailed, α = {ALPHA}.', '']
    out += report('All respondents', rows, dims)
    if is_eng:
        eng = [r for r in rows if is_eng(r)]
        if not eng:
            out += [f'Note: {how} matched no respondent, so {VALIDATOR} did not answer the questionnaire '
                    'under that ID; the second analysis is not shown. Check the ID before reporting this.', '']
        else:
            others = [r for r in rows if not is_eng(r)]
            if len(eng) > 1:
                out += [f'Warning: {how} matched {len(eng)} responses; only one respondent was expected.', '']
            out += [f'{VALIDATOR} answered the questionnaire ({len(eng)} response). State this in Section 5.6.', '']
            out += report(f'Without {VALIDATOR} ({len(eng)} response(s) excluded)', others, dims)
    else:
        out += ['Note: --validator-id was not given, so only the analysis with all respondents is shown. '
                f'If {VALIDATOR} answered the questionnaire, rerun with his respondent ID.', '']
    text = '\n'.join(out)
    sys.stdout.reconfigure(encoding='utf-8')
    print(text)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(text)


if __name__ == '__main__':
    main()
