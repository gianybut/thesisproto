// Two-page Word file for the validator: page 1 the sample sheet, page 2 the certification letter.
//
//   python ml/local/validation_sheet.py          (strips + counts, into data/local/validation_sheet/)
//   node tools/make_validation_letter.js         (needs the "docx" npm package: npm install docx)
//
// Writes data/local/validation_sheet/OcuLubak_dataset_validation.docx (footage-derived, gitignored).
// The docx package is looked up in tools/node_modules: npm install --prefix tools --no-save docx
// Text in [square brackets] is highlighted: the team fills it in before printing.
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, ShadingType, TabStopType, LeaderType, PageBreak,
} = require('docx');

const DIR = path.join(__dirname, '..', 'data', 'local', 'validation_sheet');
const counts = JSON.parse(fs.readFileSync(path.join(DIR, 'counts.json'), 'utf8'));
const N = counts.shown;
const CLASSES = [
  ['D00', 'Longitudinal crack', 'a crack that runs along the direction of the road'],
  ['D10', 'Transverse crack', 'a crack that runs across the road'],
  ['D20', 'Alligator crack', 'connected cracks that form a pattern of small blocks'],
  ['D40', 'Pothole', 'a hole or bowl-shaped break in the road surface'],
];
// The letter says how the samples were picked (counts.json, written by validation_sheet.py).
const HOW = counts.picked === 'by_hand' ? 'selected from' : 'drew at random from';
const total = CLASSES.reduce((s, [c]) => s + counts.boxes[c], 0);
const num = (n) => n.toLocaleString('en-US');
const FONT = 'Arial';
const IN = 1440;                       // DXA per inch
const WIDTH = 7.3 * IN;                // usable width: Letter, 0.6 in side margins
const STRIP_W = 7.3 * 96;              // px at 96 dpi; a strip is 3048 x 772
const STRIP_H = STRIP_W * 772 / 3048;

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: 22, ...o });
const fill = (text) => run(text, { highlight: 'yellow' });
const para = (children, o = {}) => new Paragraph({ children, spacing: { after: 160, line: 300 }, ...o });
const blank = (label, pos = WIDTH) => new Paragraph({
  children: [run(label), run('\t')],
  tabStops: [{ type: TabStopType.RIGHT, position: pos, leader: LeaderType.UNDERSCORE }],
  spacing: { after: 100 },
});

// ---- Page 1: the sample sheet ----
const sheet = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [run('ROAD DAMAGE SAMPLES FOR VISUAL VALIDATION', { bold: true, size: 26 })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 100 },
    children: [run('Each numbered picture shows one damage that the researchers marked (box) and classified. '
      + 'Please check that every picture shows the damage type named above its group.', { size: 18 })],
  }),
];
CLASSES.forEach(([code, name, what], i) => {
  sheet.push(new Paragraph({
    spacing: { before: 80, after: 40 }, keepNext: true,
    children: [
      run(`${code}  ${name}`, { bold: true, size: 21 }),
      run(`  (${what})  ·  items ${i * N + 1} to ${(i + 1) * N}`, { size: 18 }),
    ],
  }));
  sheet.push(new Paragraph({
    spacing: { after: 0 },
    children: [new ImageRun({
      type: 'png', data: fs.readFileSync(path.join(DIR, `class_${code}.png`)),
      transformation: { width: Math.round(STRIP_W), height: Math.round(STRIP_H) },
      altText: { title: `${code} samples`, description: `${N} sample pictures of ${name}`, name: `class_${code}` },
    })],
  }));
});

// ---- Page 2: the letter ----
const COLS = [1000, 3000, 3000, 3512];
const border = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
const cell = (text, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  borders: { top: border, bottom: border, left: border, right: border },
  margins: { top: 50, bottom: 50, left: 100, right: 100 },
  shading: o.head ? { type: ShadingType.CLEAR, fill: 'E8EEF5' } : undefined,
  children: [new Paragraph({
    alignment: o.right ? AlignmentType.RIGHT : AlignmentType.LEFT,
    children: [run(text, { bold: !!(o.head || o.bold), size: 20 })],
  })],
});
const row = (cells, o = {}) => new TableRow({
  children: cells.map((t, i) => cell(t, COLS[i], { ...o, right: i === 2 })),
});
const table = new Table({
  width: { size: COLS.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: COLS,
  rows: [
    row(['Code', 'Damage type', 'Marked in the dataset', 'Samples I inspected'], { head: true }),
    ...CLASSES.map(([code, name], i) => row([code, name, num(counts.boxes[code]),
      `${N} (items ${i * N + 1} to ${(i + 1) * N})`])),
    row(['Total', '', num(total), `${N * CLASSES.length}`], { bold: true }),
  ],
});
const CHECK = '☐  ';
const box = (text) => para([run(CHECK, { font: 'Segoe UI Symbol' }), run(text)],
  { indent: { left: 360 }, spacing: { after: 80 } });

const letter = [
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 280 },
    children: [run('CERTIFICATION OF DATASET VALIDATION', { bold: true, size: 28 })],
  }),
  blank('Date: ', 3 * IN),
  para([run('TO WHOM IT MAY CONCERN:', { bold: true })], { spacing: { before: 200, after: 200 } }),
  para([
    run('This is to certify that I examined the road damage image dataset prepared for the thesis study “OcuLubak: '),
    fill('[full thesis title]'), run('” by '), fill('[names of the researchers]'), run(' of '),
    fill('[program and school]'), run('.'),
  ], { alignment: AlignmentType.JUSTIFIED }),
  para([run(`The dataset has ${num(counts.frames)} road images taken from survey videos that the researchers recorded `
    + `from a vehicle. On these images the researchers marked ${num(total)} damages and classified each one into one of `
    + 'the four damage types of the Road Damage Dataset 2022 (RDD2022):')], { alignment: AlignmentType.JUSTIFIED }),
  table,
  para([run(`I visually inspected the ${N * CLASSES.length} sample pictures on the attached sheet, which the researchers `
    + `${HOW} the marked damages, ${N} for each damage type. Based on this inspection, I find that the `
    + 'damages shown are correctly identified and classified, as follows:')],
  { alignment: AlignmentType.JUSTIFIED, spacing: { before: 200, after: 120, line: 300 } }),
  box(`All ${N * CLASSES.length} items are correct.`),
  new Paragraph({
    indent: { left: 360 }, spacing: { after: 160 },
    tabStops: [{ type: TabStopType.RIGHT, position: WIDTH, leader: LeaderType.UNDERSCORE }],
    children: [run(CHECK, { font: 'Segoe UI Symbol' }), run('All items are correct except item nos. '), run('\t')],
  }),
  blank('Remarks: '),
  blank(''),
  para([run('This certification is issued at the request of the researchers for academic purposes only.')],
    { spacing: { before: 200, after: 480 } }),
  blank('', 3.6 * IN),
  para([run('Signature over printed name', { size: 20 })], { spacing: { after: 160 } }),
  blank('Position / Designation: ', 5 * IN),
  blank('Office / Agency: ', 5 * IN),
  blank('PRC License No. (if any): ', 5 * IN),
];

const doc = new Document({
  creator: 'OcuLubak research team', title: 'Dataset validation: sample sheet and certification',
  styles: { default: { document: { run: { font: FONT, size: 22 } } } },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 0.5 * IN, bottom: 0.5 * IN, left: 0.6 * IN, right: 0.6 * IN },
      },
    },
    children: [...sheet, ...letter],
  }],
});
const out = path.join(DIR, 'OcuLubak_dataset_validation.docx');
Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(out, buf); console.log(out, buf.length, 'bytes'); });
