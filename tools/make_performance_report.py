"""Build results/OcuLubak_system_performance.pdf: the whole measured performance of the system, explained.

    .venv\\Scripts\\python tools\\make_performance_report.py

Numbers come from results/system_level_evaluation.json (frame-level, classifier, comparison) and, for the
parts outside detection, from the files named in the Sources section. Nothing is computed from the test set here.
"""

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,  # noqa: E402
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'OcuLubak_system_performance.pdf'
TMP = ROOT / 'results' / '_report_figs'
D = json.loads((ROOT / 'results' / 'system_level_evaluation.json').read_text())

BLUE = '#2a78d6'       # palette slot 1: the deployed system
GREY = '#9b9a94'       # comparison marks
INK, INK2 = '#0b0b0b', '#52514e'
RULE = '#d9d8d3'

FONTS = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Body', str(FONTS / 'arial.ttf')))
pdfmetrics.registerFont(TTFont('Body-Bold', str(FONTS / 'arialbd.ttf')))
pdfmetrics.registerFont(TTFont('Body-Italic', str(FONTS / 'ariali.ttf')))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Body-Bold', italic='Body-Italic', boldItalic='Body-Bold')
plt.rcParams.update({'font.family': 'Arial', 'font.size': 9, 'text.color': INK, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.edgecolor': RULE})

S = {
    'title': ParagraphStyle('t', fontName='Body-Bold', fontSize=20, leading=24, textColor=INK, spaceAfter=4),
    'sub': ParagraphStyle('s', fontName='Body', fontSize=10.5, leading=14, textColor=INK2, spaceAfter=14),
    'h1': ParagraphStyle('h1', fontName='Body-Bold', fontSize=14, leading=18, textColor=INK, spaceBefore=14, spaceAfter=6,
                         keepWithNext=1),
    'h2': ParagraphStyle('h2', fontName='Body-Bold', fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4,
                         keepWithNext=1),
    'p': ParagraphStyle('p', fontName='Body', fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    'small': ParagraphStyle('sm', fontName='Body', fontSize=8, leading=10.5, textColor=INK2, spaceAfter=4),
    'cell': ParagraphStyle('c', fontName='Body', fontSize=8.3, leading=10.5, textColor=INK),
    'cellb': ParagraphStyle('cb', fontName='Body-Bold', fontSize=8.3, leading=10.5, textColor=INK),
    'bullet': ParagraphStyle('b', fontName='Body', fontSize=9.5, leading=13.5, textColor=INK, leftIndent=12,
                             bulletIndent=2, spaceAfter=3),
    'cap': ParagraphStyle('cap', fontName='Body-Italic', fontSize=8.5, leading=11, textColor=INK2, spaceBefore=6,
                          spaceAfter=3, keepWithNext=1),
}


def P(t, s='p'):
    return Paragraph(t, S[s])


def bullets(items):
    return [Paragraph(t, S['bullet'], bulletText='•') for t in items]


def ci(c, pct=False):
    if not c:
        return '—'
    return f'{100 * c[0]:.1f}–{100 * c[1]:.1f}%' if pct else f'{c[0]:.3f}–{c[1]:.3f}'


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0, c - h), min(1, c + h)]


def table(rows, widths, header=True, bold_first_col=False, zebra=True, highlight_row=None):
    data = []
    for i, r in enumerate(rows):
        st = 'cellb' if (header and i == 0) else 'cell'
        data.append([Paragraph(str(x), S['cellb'] if (bold_first_col and j == 0 and i > 0) else S[st])
                     for j, x in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, 0), 0.8, colors.HexColor(INK2)),
             ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor(RULE)), ('TOPPADDING', (0, 0), (-1, -1), 3),
             ('BOTTOMPADDING', (0, 0), (-1, -1), 3), ('LEFTPADDING', (0, 0), (-1, -1), 4),
             ('RIGHTPADDING', (0, 0), (-1, -1), 4)]
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f4f4f1')))
    if highlight_row is not None:
        style.append(('BACKGROUND', (0, highlight_row), (-1, highlight_row), colors.HexColor('#e3eefb')))
    t.setStyle(TableStyle(style))
    t.spaceAfter = 8
    return t


def yesno(v):
    return '<b>Yes</b>' if v else 'No'


# ---------------------------------------------------------------- numbers
sysT = D['fusion_cls']['test']
fusT = D['fusion']['test']
sysV = D['fusion_cls']['val']
allV = D['val_all_1624']['fusion_cls']
box_sys = D['fusion_cls']['box_check_test']
box_fus = D['fusion']['box_check_test']
cm = D['classifier_heldout_test_cm']
CODES = ['D00', 'D10', 'D20', 'D40']
NAMES = {'D00': 'Longitudinal crack (D00)', 'D10': 'Transverse crack (D10)', 'D20': 'Alligator crack (D20)',
         'D40': 'Pothole (D40)'}
pres, typ = sysT['present'], sysT['typed']
clf_right = sum(cm[i][i] for i in range(4))
clf_ci = wilson(clf_right, 99)


# ---------------------------------------------------------------- charts
def chart_criterion(path):
    items = [
        ('Detection accuracy', pres['acc'], pres['acc_ci']),
        ('Detection precision', pres['p'], pres['p_ci']),
        ('Detection recall', pres['r'], pres['r_ci']),
        ('Detection F1-score', pres['f1'], pres['f1_ci']),
        ('Correct-type F1-score', typ['f1'], typ['f1_ci']),
        ('Classification accuracy\n(matched detections)', box_sys['cls_acc'], box_sys['cls_ci']),
        ('Classifier alone\n(99 held-out crops)', clf_right / 99, clf_ci),
    ][::-1]
    fig, ax = plt.subplots(figsize=(6.4, 3.3), dpi=220)
    y = range(len(items))
    for i, (lab, v, c) in enumerate(items):
        ax.barh(i, v, height=0.5, color=BLUE, zorder=2)
        ax.plot([c[0], c[1]], [i, i], color=INK, lw=1.2, zorder=3)
        ax.plot([c[0], c[0]], [i - 0.12, i + 0.12], color=INK, lw=1.2, zorder=3)
        ax.plot([c[1], c[1]], [i - 0.12, i + 0.12], color=INK, lw=1.2, zorder=3)
        ax.text(c[1] + 0.015, i, f'{v:.3f}', va='center', fontsize=8.5, color=INK)
    top = len(items) - 0.55
    ax.axvline(0.80, color=INK2, lw=1, ls=(0, (4, 3)), zorder=4)
    ax.text(0.805, top, '0.80 criterion', fontsize=7.5, color=INK2, va='bottom', ha='left')
    ax.axvline(0.767, color=GREY, lw=1, ls=(0, (1, 2)), zorder=4)
    ax.text(0.762, top, 'accuracy of "never report damage" (0.767)', fontsize=7.5, color=INK2, va='bottom', ha='right')
    ax.set_yticks(list(y))
    ax.set_yticklabels([i[0] for i in items])
    ax.set_xlim(0, 1.1)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_ylim(-0.6, len(items) - 0.05)
    ax.set_xlabel('Value on the local test set (bars) with 95% confidence interval (lines)')
    ax.grid(axis='x', color='#ecebe7', lw=0.6, zorder=0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def chart_compare(path):
    rows = [('Deployed system', sysT['present'], True)]
    names = {'Teacher (ours, RDD2022 only, YOLOv8m)': 'RDD2022-only teacher',
             'SreekarAditya YOLOv8s RDD2022 (seed 0)': 'Public YOLOv8s (RDD2022)',
             'SreekarAditya YOLOv12s RDD2022 (seed 0)': 'Public YOLOv12s (RDD2022)',
             'Stand-in (external 7-class YOLOv8n RDD2022)': 'Stand-in YOLOv8n'}
    for c in D['comparators']:
        rows.append((names[c['title']], c['test']['present'], False))
    rows = rows[::-1]
    fig, ax = plt.subplots(figsize=(6.4, 2.5), dpi=220)
    for i, (lab, r, me) in enumerate(rows):
        col = BLUE if me else GREY
        ax.plot(r['f1_ci'], [i, i], color=col, lw=2, solid_capstyle='round', zorder=2)
        ax.scatter([r['f1']], [i], s=46, color=col, edgecolor='white', linewidth=1.5, zorder=3)
        ax.text(r['f1_ci'][1] + 0.012, i, f"{r['f1']:.3f}", va='center', fontsize=8.5, color=INK)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlim(0.25, 0.85)
    ax.set_xlabel('Frame-level F1-score for damage present, 270 test frames (dot) with 95% CI (line)')
    ax.grid(axis='x', color='#ecebe7', lw=0.6, zorder=0)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Body', 7.5)
    canvas.setFillColor(colors.HexColor(INK2))
    canvas.drawString(18 * mm, 10 * mm, 'OcuLubak: system performance report, 15 November 2026')
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f'Page {doc.page}')
    canvas.restoreState()


def build():
    TMP.mkdir(exist_ok=True)
    f1, f2 = TMP / 'criterion.png', TMP / 'compare.png'
    chart_criterion(f1)
    chart_compare(f2)
    W = A4[0] - 36 * mm
    st = []

    # ---------------- title + summary
    st += [P('OcuLubak: How Well the System Performs', 'title'),
           P('Measured performance of the deployed road damage detection system, explained. '
             'Results as of 15 November 2026.', 'sub')]
    st.append(P('Summary', 'h1'))
    st.append(P(
        'OcuLubak works as a complete pipeline: a phone records the road and the GPS track, the server finds and '
        'classifies the damage, and every record lands on the map at the right time and place. '
        '<b>When it finds a damage, it names the type correctly most of the time; what holds it back is finding the '
        'damage in the first place.</b> On 270 test frames from roads it never saw in training, it flagged damage '
        'in 34 of the 63 frames that have damage (recall 0.540) and gave a false alarm in 24 of the 207 frames '
        'without damage. Potholes are the weakest class: it found a pothole in only 1 of 17 frames that hold one.'))
    kpi = [['Measure (local test set)', 'Result', 'Meets 0.80?'],
           ['Detection accuracy (damage present)', f"{pres['acc']:.3f}", 'Yes, by 0.004 (see note)'],
           ['Detection precision / recall / F1-score', f"{pres['p']:.3f} / {pres['r']:.3f} / {pres['f1']:.3f}", 'No'],
           ['Correct-type F1-score', f"{typ['f1']:.3f}", 'No'],
           ['Classification accuracy of detected damage', f"{100 * box_sys['cls_acc']:.1f}% (23 of 25)", '<b>Yes</b>'],
           ['Second-stage classifier alone (held-out crops)', f'{100 * clf_right / 99:.1f}% (85 of 99)', '<b>Yes</b>'],
           ['Time and location stored with each record', '50 of 50 correct', 'Yes (automatic check)'],
           ['User acceptance (52 DPWH personnel)', '4.62 of 5, Strongly Agree', 'Hypothesis supported']]
    st.append(table(kpi, [W * 0.47, W * 0.30, W * 0.23]))
    st.append(P('Note: 207 of the 270 test frames show no damage, so a system that never reported anything would '
                'already score an accuracy of 0.767. The 0.804 is therefore only slightly better than doing nothing, '
                'and precision, recall and F1-score are the measures that show how well the system detects.', 'small'))

    # ---------------- how it was tested
    st.append(P('1. How the system was tested', 'h1'))
    st += bullets([
        '<b>What was tested.</b> The deployed system exactly as it runs: three YOLOv8 models whose boxes are '
        'combined (weighted box fusion), a confidence threshold of 0.25, and a second-stage classifier that sets '
        'the damage type of each box. Nothing was retrained or tuned for this evaluation.',
        '<b>Test set.</b> 270 frames from three route groups (G05, G13, G15) that were never used for training or for '
        'choosing the model. 63 frames show damage (99 reviewed boxes); 207 show none. Labels were reviewed by one person.',
        '<b>Frame level.</b> Each frame counts once. A frame is "with damage" if it has at least one reviewed box, and the '
        'system "reports damage" if it puts at least one box on it. This matches how the system is used: an engineer '
        'looks at a flagged moment in the video, not at individual boxes.',
        '<b>Correct type.</b> A stricter version: a frame with damage counts as found only if one of the system\'s boxes '
        'lies on a reviewed damage (its centre inside the reviewed box, or overlap IoU ≥ 0.25) <i>and</i> has the same class.',
        '<b>The four measures.</b> Accuracy = share of all frames judged correctly. Precision = of the frames the system '
        'flagged, how many really show damage. Recall = of the frames with damage, how many the system flagged. '
        'F1-score = the balance of precision and recall. Every value has a 95% confidence interval (Wilson; '
        'bootstrap for F1), which shows how far the true value could plausibly be from the measured one with this few frames.',
        '<b>Acceptance criterion.</b> Performance of at least 0.80 in accuracy, precision, recall or F1-score. These '
        'system-level measures were adopted after the initial box-level evaluation, at the adviser\'s recommendation, '
        'to reflect how the system is used.',
    ])

    # ---------------- detection
    st.append(P('2. Finding damage', 'h1'))
    rows = [['Measure', 'TP / FP / FN / TN', 'Accuracy', 'Precision', 'Recall', 'F1-score']]
    for lab, r in [('Damage present', pres), ('Damage present, correct type', typ),
                   ('Correct type, fusion without the classifier', fusT['typed'])]:
        rows.append([lab, f"{r['tp']} / {r['fp']} / {r['fn']} / {r['tn']}",
                     f"{r['acc']:.3f}<br/>({ci(r['acc_ci'])})", f"{r['p']:.3f}<br/>({ci(r['p_ci'])})",
                     f"{r['r']:.3f}<br/>({ci(r['r_ci'])})", f"{r['f1']:.3f}<br/>({ci(r['f1_ci'])})"])
    rows.append(['Reference: report nothing', '0 / 0 / 63 / 207', '0.767<br/>(0.713–0.813)', '—', '0.000', '0.000'])
    st.append(P('Table 1. Frame-level results on the 270 test frames (threshold 0.25). TP = damaged frames flagged, '
                'FP = clean frames flagged, FN = damaged frames missed, TN = clean frames left alone.', 'cap'))
    st.append(table(rows, [W * 0.27, W * 0.17, W * 0.14, W * 0.14, W * 0.14, W * 0.14], highlight_row=1))
    st.append(P(
        'Read across the first row: the system flagged 58 frames, 34 of them correctly, so a little over half of its '
        'alerts are real damage (precision 0.586) and it catches a little over half of the damaged frames (recall 0.540). '
        'When the type must also be right, it found 23 of the 63 damaged frames. Without the classifier the fusion '
        'found 25, so the classifier did not help on these frames; a difference of two frames is within the uncertainty.'))
    st.append(Image(str(f1), width=W, height=W * 3.3 / 6.4))
    st.append(P('Figure 1. Each headline measure against the 0.80 criterion. Only detection accuracy and the two '
                'classification measures reach it; accuracy\'s interval also covers the 0.767 of a system that reports nothing.',
                'cap'))

    # ---------------- per class
    st.append(P('3. Each type of damage', 'h1'))
    rows = [['Damage class', 'Frames with it', 'TP / FP / FN / TN', 'Accuracy', 'Precision', 'Recall', 'F1-score']]
    for c in CODES:
        r = sysT['per_class_typed'][c]
        rows.append([NAMES[c], str(r['tp'] + r['fn']), f"{r['tp']} / {r['fp']} / {r['fn']} / {r['tn']}",
                     f"{r['acc']:.3f}", f"{r['p']:.3f}<br/>({ci(r['p_ci'])})", f"{r['r']:.3f}<br/>({ci(r['r_ci'])})",
                     f"{r['f1']:.3f}"])
    st.append(P('Table 2. Per class, deployed system: a frame counts for a class if it has a reviewed box of that class, '
                'and as found if a box of that class lies on one.', 'cap'))
    st.append(table(rows, [W * 0.24, W * 0.1, W * 0.17, W * 0.1, W * 0.14, W * 0.14, W * 0.11]))
    st += bullets([
        '<b>Longitudinal cracks</b> are found best (recall 0.538). They are the most common class in training.',
        '<b>Potholes</b> are the weakest: found in 1 of 17 frames, and 10 of the 11 frames where the system reported a '
        'pothole had none. This is the main thing to improve.',
        '<b>Alligator cracks</b> are rarely reported, but when they are, they are right (6 of 7 frames, precision 0.857).',
        '<b>Transverse cracks</b> occur in only 5 test frames, so their numbers are very uncertain.',
        'The per-class accuracies (0.90–0.94) look high only because each class is absent from most frames.',
    ])

    # ---------------- classification
    st.append(P('4. Naming the damage type', 'h1'))
    st.append(P(
        f"Among the 25 detections that overlapped a reviewed damage (IoU ≥ 0.50), the deployed system gave "
        f"<b>23 the correct type: 92.0%</b> (95% CI {ci(box_sys['cls_ci'], True)}). Both errors were transverse cracks "
        f"labelled potholes. The fusion alone, before the classifier, had 24 of 25 right (96.0%, CI {ci(box_fus['cls_ci'], True)}). "
        f"These figures cover only the damage that was found."))
    st.append(P(
        f"The second-stage classifier was also tested alone on the crops of all 99 reviewed test boxes, which it never "
        f"saw in training or selection: <b>{clf_right} of 99 correct, {100 * clf_right / 99:.1f}%</b> (95% CI {ci(clf_ci, True)})."))
    rows = [['Reviewed class \\ Predicted', 'D00', 'D10', 'D20', 'D40', 'Recall']]
    for i, c in enumerate(CODES):
        n = sum(cm[i])
        rows.append([f'{NAMES[c]}, {n}', *[str(v) for v in cm[i]], f'{100 * cm[i][i] / n:.1f}%'])
    rows.append(['Precision', *[f'{100 * cm[j][j] / sum(cm[i][j] for i in range(4)):.1f}%' for j in range(4)],
                 f'All: {100 * clf_right / 99:.1f}%'])
    st.append(KeepTogether([P('Table 3. Second-stage classifier on the 99 held-out test crops.', 'cap'),
                            table(rows, [W * 0.32, W * 0.12, W * 0.12, W * 0.12, W * 0.12, W * 0.2], bold_first_col=False)]))
    st.append(P(
        'It recognises potholes and longitudinal cracks almost perfectly, but it calls 4 of 8 transverse cracks and 4 of '
        '34 alligator cracks potholes. One likely reason it does not help inside the pipeline: it was trained on crops '
        'cut with 25% extra margin, while the system hands it the detector\'s boxes with no margin.'))

    # ---------------- comparison
    st.append(P('5. Compared with pretrained models', 'h1'))
    st.append(P(
        'The same frame-level test was run on four models that were not fine-tuned on local roads. Each was given its '
        'own best threshold, chosen on the validation frames for frame-level F1; the deployed system kept its 0.25, '
        'chosen earlier on box-level F1. This setup favours the pretrained models.'))
    rows = [['Model', 'Threshold', 'Accuracy', 'Precision', 'Recall', 'F1 (95% CI)', 'F1, correct type']]
    rows.append(['<b>Deployed system</b>', '0.25', f"{pres['acc']:.3f}", f"{pres['p']:.3f}", f"{pres['r']:.3f}",
                 f"{pres['f1']:.3f} ({ci(pres['f1_ci'])})", f"{typ['f1']:.3f}"])
    short = {'Teacher (ours, RDD2022 only, YOLOv8m)': 'RDD2022-only teacher (ours, YOLOv8m)',
             'SreekarAditya YOLOv8s RDD2022 (seed 0)': 'Public YOLOv8s RDD2022 (SreekarAditya)',
             'SreekarAditya YOLOv12s RDD2022 (seed 0)': 'Public YOLOv12s RDD2022 (SreekarAditya)',
             'Stand-in (external 7-class YOLOv8n RDD2022)': 'Stand-in YOLOv8n (external)'}
    for c in D['comparators']:
        a, b = c['test']['present'], c['test']['typed']
        rows.append([short[c['title']], f"{c['threshold']:.2f}", f"{a['acc']:.3f}", f"{a['p']:.3f}", f"{a['r']:.3f}",
                     f"{a['f1']:.3f} ({ci(a['f1_ci'])})", f"{b['f1']:.3f}"])
    st.append(P('Table 4. All models on the same 270 test frames.', 'cap'))
    st.append(table(rows, [W * 0.27, W * 0.12, W * 0.1, W * 0.1, W * 0.09, W * 0.2, W * 0.12], highlight_row=1))
    st.append(Image(str(f2), width=W, height=W * 2.5 / 6.4))
    st.append(P('Figure 2. F1-score for damage present with confidence intervals. All intervals overlap.', 'cap'))
    st.append(P(
        'The deployed system is <b>comparable to the best public RDD2022 checkpoints</b> (overlapping confidence '
        'intervals) and better than the RDD2022-only model and the stand-in model at detecting damage. It does not '
        'outperform all of them: the public YOLOv12s scored a higher F1 (0.603), and for the correct type both public '
        'models and the teacher (0.448) are slightly ahead of the system (0.418). None of these differences can be '
        'separated with 63 damaged test frames.'))

    # ---------------- validation, box level, foreign
    st.append(P('6. Other views of the same models', 'h1'))
    st.append(P('Validation versus test', 'h2'))
    st.append(P(
        f"The model and threshold were chosen on 270 reviewed validation frames, where the system scored F1 "
        f"{sysV['present']['f1']:.3f} for damage present. On the unseen test frames it scored {pres['f1']:.3f}. The drop "
        f"is the usual optimism of a selection set. On all 1,624 validation frames it scored {allV['present']['f1']:.3f} "
        f"(correct type {allV['typed']['f1']:.3f})."))
    st.append(P('Box-level results (kept as evidence, not the headline)', 'h2'))
    st.append(P(
        f"Counted box by box (each reviewed damage matched to one detection of the same class at IoU ≥ 0.50), the "
        f"deployed system had precision {box_sys['tp'] / (box_sys['tp'] + box_sys['fp']):.2f} and recall "
        f"{box_sys['tp'] / box_sys['boxes']:.2f}: 23 of its 78 boxes matched, and 76 of 99 reviewed damages were missed. "
        "The box-level mean average precision measured on 11 November 2026, mAP@50 = 0.173 (fusion alone), stays in "
        "the project records as evidence but is no longer reported in the manuscript."))
    st.append(P('Foreign roads (RDD2022, six countries)', 'h2'))
    st.append(P(
        'Each fused model alone was tested on 3,277 public RDD2022 images. Box-level precision and recall: v2b 0.323 / '
        '0.269 (not a held-out result, since its starting checkpoint very likely saw these images), v3 0.337 / 0.305, '
        'S5_v8m_1920 0.411 / 0.369.'))

    # ---------------- rest of the system
    st.append(P('7. The rest of the system', 'h1'))
    rows = [['Part', 'Result', 'Status'],
            ['Damage log: time of each record', '50 of 50 sampled R07 records match their video frame (100%; 95% CI 92.9–100%)', 'Measured'],
            ['Damage log: location against the GPS track', '50 of 50 lie on the track at their video time; mean 0.15 m, max 0.44 m', 'Measured'],
            ['Damage log: record precision, type, duplicates', '50 R07 records drawn (seed 42); 5 duplicate-candidate pairs found automatically', 'Pending manual review'],
            ['AI check flags', '36 of 112 R07 records flagged as likely not damage', 'Pending review'],
            ['Positional error against the real damage', 'Field validation not carried out', 'Not measured'],
            ['Processing speed', '590 s recording analysed in 729 s (1.2× its length; 0.206 s per analysed frame), 112 records', 'Measured (1 survey)'],
            ['Label quality', 'DPWH engineer confirmed 40 of 40 hand-picked boxes, 10 per class', 'Measured'],
            ['User acceptance', '52 DPWH Cavite 2nd DEO personnel: overall 4.62 (SD 0.22), t(51) = 39.83, p &lt; .001', 'Hypothesis supported']]
    st.append(table(rows, [W * 0.3, W * 0.5, W * 0.2]))
    rows = [['Quality characteristic', 'Mean', 'SD', 'Interpretation'],
            ['Functional suitability', '4.62', '0.26', 'Strongly Agree'],
            ['Interaction capability', '4.62', '0.27', 'Strongly Agree'],
            ['Performance efficiency', '4.60', '0.27', 'Strongly Agree'],
            ['Compatibility, reliability, and security', '4.64', '0.26', 'Strongly Agree'],
            ['Overall usefulness', '4.61', '0.23', 'Strongly Agree'],
            ['Overall', '4.62', '0.22', 'Strongly Agree']]
    st.append(KeepTogether([P('Table 5. User acceptance testing (five-point scale, criterion mean 3.41).', 'cap'),
                            table(rows, [W * 0.5, W * 0.15, W * 0.15, W * 0.2])]))
    st.append(P('The respondents rated the system highly, but these are perceptions after a demonstration; they '
                'should be read next to the measured detection results above.', 'small'))

    # ---------------- criterion scorecard
    st.append(P('8. The 0.80 criterion, measure by measure', 'h1'))
    rows = [['Measure', 'Value', '≥ 0.80?']]
    for lab, v in [('Detection accuracy', pres['acc']), ('Detection precision', pres['p']), ('Detection recall', pres['r']),
                   ('Detection F1-score', pres['f1']), ('Correct-type accuracy', typ['acc']),
                   ('Correct-type precision', typ['p']), ('Correct-type recall', typ['r']), ('Correct-type F1-score', typ['f1']),
                   ('Classification accuracy (pipeline)', box_sys['cls_acc']), ('Classifier alone (held-out crops)', clf_right / 99)]:
        rows.append([lab, f'{v:.3f}', yesno(v >= 0.80)])
    rows.append(['Record-level measures (R07)', 'pending', '—'])
    st.append(table(rows, [W * 0.55, W * 0.2, W * 0.25]))

    # ---------------- limitations
    st.append(P('9. What limits these results', 'h1'))
    st += bullets([
        '<b>Small test set:</b> only 63 damaged frames, 5 with a transverse crack and 17 with a pothole. Intervals are '
        'about ±12 percentage points wide.',
        '<b>Potholes:</b> found in 1 of 17 test frames.',
        '<b>Classifier padding mismatch:</b> trained on padded crops, given unpadded boxes in the system.',
        '<b>Measures adopted later:</b> the frame-level measures were adopted after the initial box-level evaluation, at '
        'the adviser\'s recommendation; they were computed on the same frozen system and test frames.',
        '<b>Near zone only:</b> results cover the strip of road just ahead, not damage farther away.',
        '<b>One reviewer</b> labelled all validation and test frames.',
    ])

    # ---------------- sources
    st.append(P('Sources', 'h1'))
    st.append(P(
        'Frame-level, classifier and comparison results: results/system_level_evaluation.md and .json '
        '(ml/local/system_level_eval.py). Box-level and foreign results: results/test_evaluation.md. Decision to report '
        'system-level measures: docs/decisions.md (15 November 2026). Damage log, processing, expert check and user '
        'acceptance: manuscript Chapter V, Sections 5.2–5.6.', 'small'))

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=18 * mm, title='OcuLubak System Performance',
                            author='OcuLubak research team', subject='Measured performance of the deployed system')
    doc.build(st, onFirstPage=footer, onLaterPages=footer)
    for f in (f1, f2):
        f.unlink()
    TMP.rmdir()
    print(OUT)


if __name__ == '__main__':
    build()
