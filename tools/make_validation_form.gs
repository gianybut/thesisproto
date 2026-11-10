/**
 * Builds the expert-check Google Form for the reviewed road-damage labels (Step 7.3).
 *
 * Setup (see the steps Claude Code gave the team, also in the comment at the end):
 *   1. Upload data/local/annotation_form/images/*.jpg AND form_items.csv into ONE new Google Drive
 *      folder. Do NOT upload answer_key.csv (it holds the answers).
 *   2. Put that folder's ID (the last part of its URL) in FOLDER_ID below.
 *   3. script.google.com > New project > paste this file > Run buildValidationForm > allow access.
 *   4. View > Logs (or Execution log) shows the form's edit link, send link and response sheet.
 *
 * Each box: an image item (its ID; the picture shows the whole frame and a close-up, the box in
 * the same magenta for every class) followed by a REQUIRED multiple-choice question with five
 * answers. Questions are in the order of form_items.csv (already random); the form's own shuffle
 * setting stays OFF, so every respondent sees the same order and IDs match the answer key.
 *
 * Apps Script stops a run after 6 minutes, and 100 images take longer. So the script works in
 * parts: it remembers its form, stops by itself after about 5 minutes ("Run again to continue" in
 * the log), and each new run of buildValidationForm adds only what is still missing. When the
 * log says "Form complete" it is done. To continue a form made before this change, put its ID
 * (the long part of its edit URL, between /d/ and /edit) in FORM_ID. startOver() forgets the
 * remembered form so the next run makes a new one.
 */

const FOLDER_ID = '1AtiNXq1sWc9SVwy_loInwgXFdSwXqOc8';
const FORM_ID = '';     // optional: an existing, unfinished form to continue (see above)
const TIME_LIMIT_MS = 5 * 60 * 1000;
const FORM_TITLE = 'Road damage labels: expert check';
const PER_PAGE = 10;   // boxes per page, so the form loads quickly
const CHOICES = [
  'D00 Longitudinal crack',
  'D10 Transverse crack',
  'D20 Alligator crack',
  'D40 Pothole',
  'Not road damage',
];

function buildValidationForm() {
  const started = Date.now();
  const props = PropertiesService.getScriptProperties();
  if (FOLDER_ID.indexOf('PASTE') === 0) throw new Error('Set FOLDER_ID first (step 2).');
  const folder = DriveApp.getFolderById(FOLDER_ID);
  const csvFiles = folder.getFilesByName('form_items.csv');
  if (!csvFiles.hasNext()) throw new Error('form_items.csv is not in the folder.');
  if (folder.getFilesByName('answer_key.csv').hasNext()) {
    throw new Error('answer_key.csv is in the folder. Remove it: the validator must not see the answers.');
  }
  const rows = Utilities.parseCsv(csvFiles.next().getBlob().getDataAsString());
  const head = rows.shift();
  const iId = head.indexOf('id'), iImg = head.indexOf('image');
  const items = rows.filter(function (r) { return r.length > 1 && r[iId]; })
                    .map(function (r) { return { id: r[iId], image: r[iImg] }; });

  const formId = FORM_ID || props.getProperty('formId');
  let form;
  if (formId) {
    form = FormApp.openById(formId);
    Logger.log('Continuing the form ' + form.getEditUrl());
  } else {
    form = FormApp.create(FORM_TITLE);
    props.setProperty('formId', form.getId());
    Logger.log('New form ' + form.getEditUrl());
  }
  if (FORM_ID) props.setProperty('formId', FORM_ID);

  // What is already in the form, by type and title. A run that was stopped leaves a complete
  // prefix, so whatever is missing is always at the end and appending keeps the order.
  const have = {};
  form.getItems().forEach(function (x) { have[x.getType() + '|' + x.getTitle()] = true; });
  const has = function (type, title) { return have[type + '|' + title] === true; };
  const T = FormApp.ItemType;

  if (!has(T.TEXT, 'Your name')) {
    setUpForm(form, items.length);
  }

  for (let i = 0; i < items.length; i++) {
    const it = items[i];
    const question = it.id + ': what is inside the magenta box?';
    if (has(T.MULTIPLE_CHOICE, question)) continue;
    if (Date.now() - started > TIME_LIMIT_MS) {
      Logger.log('Stopped at box ' + (i + 1) + ' of ' + items.length + ' (time limit). Run again to continue.');
      return;
    }
    const page = 'Boxes ' + (i + 1) + ' to ' + Math.min(i + PER_PAGE, items.length);
    if (i > 0 && i % PER_PAGE === 0 && !has(T.PAGE_BREAK, page)) {
      form.addPageBreakItem().setTitle(page);
    }
    if (!has(T.IMAGE, it.id)) {
      const files = folder.getFilesByName(it.image);
      if (!files.hasNext()) throw new Error('Missing image ' + it.image + ' in the folder.');
      form.addImageItem()
          .setTitle(it.id)
          .setImage(files.next().getBlob())
          .setAlignment(FormApp.Alignment.CENTER)
          .setWidth(740);
    }
    form.addMultipleChoiceItem()
        .setTitle(question)
        .setChoiceValues(CHOICES)
        .setRequired(true);
  }

  let sheetUrl;
  try {
    sheetUrl = SpreadsheetApp.openById(form.getDestinationId()).getUrl();
  } catch (e) {
    const sheet = SpreadsheetApp.create(FORM_TITLE + ' (responses)');
    form.setDestination(FormApp.DestinationType.SPREADSHEET, sheet.getId());
    sheetUrl = sheet.getUrl();
  }
  Logger.log('Form complete: ' + items.length + ' boxes.');
  Logger.log('Edit the form:   ' + form.getEditUrl());
  Logger.log('Send this link:  ' + form.getPublishedUrl());
  Logger.log('Responses sheet: ' + sheetUrl);
}

function setUpForm(form, n) {
  form.setDescription(
    'Each picture shows one marked area (magenta box) on a road photographed from a vehicle: the whole ' +
    'picture on top and a close-up below. Choose what is inside the box.\n\n' +
    'D00 Longitudinal crack: a crack running along the road (in the driving direction).\n' +
    'D10 Transverse crack: a crack running across the road.\n' +
    'D20 Alligator crack: connected cracks forming a mesh of small pieces.\n' +
    'D40 Pothole: a hole or missing part of the surface.\n' +
    'Not road damage: anything else (patch or repair without a hole or crack, stain, shadow, marking, object).\n\n' +
    'There are ' + n + ' boxes. Every question is required.');
  form.setShuffleQuestions(false);
  form.setProgressBar(true);
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.addTextItem().setTitle('Your name').setRequired(true);
}

/** Forget the remembered form; the next buildValidationForm run makes a new one. */
function startOver() {
  PropertiesService.getScriptProperties().deleteProperty('formId');
  Logger.log('Forgotten. The next run of buildValidationForm makes a new form.');
}

/*
 * After the validator submits: open the responses sheet > File > Download > CSV, save it as
 * data/local/annotation_form/responses.csv and run:  python ml/local/annotation_agreement.py
 */
