# design.md

The authority on every visual decision in the OcuLubak web frontend. It records the redesign
direction agreed in Stage 1 (`redesign-direction.md`). Every value here is a token in `:root` of
`src/index.css`; components use the tokens, never their own values.

## 1. Product context

A web application for local road maintenance staff to find and locate road damage without watching hours of survey video.

The user uploads a dashcam or road survey video. The system analyses it and returns a map showing where potholes and cracks were found.

Primary users are engineers and maintenance personnel at a municipal engineering office. They are not developers and they are not data scientists.

Most sessions are one task: upload a video, wait, look at the map, export the list. Sessions happen on a desktop in an office, occasionally on a phone in the field.

The value is that a two-hour survey becomes a located list in minutes. Nothing about the interface should require understanding how the detection model works.

## 2. Principles

1. One main action per screen: at most one filled primary button per view.
2. Content first: a page header is one line (title plus actions). Explanations go into hint text, empty states, or a closed "How this works".
3. Group with space and surfaces, not lines. Dividers only between rows inside a list or table.
4. Show what is needed now, reveal the rest ("More" menu, closed optional sections).
5. Actions look like what they do: buttons act, links navigate, red means data loss.
6. Status is always icon plus words. Colour never carries meaning alone.
7. Map colours are data: Okabe-Ito colours only on the map (dots, legend, popup swatch).
8. Same pattern everywhere.

## 3. Voice

Plain, specific, calm. Write like a competent friend, not like a marketing page.

- Name real things. Real places, real times.
- Buttons name their outcome ("Upload video", "Save points and place damage"). Never "Submit", "Get started" or "Learn more".
- No hype adjectives, and no jargon in the main UI ("inference", "confidence threshold", "georeference"); "Place on the map" is fine.
- Sentence case everywhere, including buttons and headings.

## 4. Colour (contrast measured, WCAG 2.1)

Calm, modern, lighter blue. Every colour is a token in `:root`; map code reads them with `cssVar()` (`src/theme.js`).

| Token | Hex | Use | Contrast |
|---|---|---|---|
| `--color-bg` | #F6F8FB | Page background | |
| `--color-surface` | #FFFFFF | Header, cards, panels, inputs | |
| `--color-subtle` | #F1F5F9 | Table heads, skeletons, hover fills | muted 4.95 |
| `--color-ink` | #1E293B | Headings and body | 14.63 on white |
| `--color-muted` | #5B6B82 | Hints, meta lines | 4.77+ on every surface (#64748B failed on bg and primary-soft) |
| `--color-primary` / `-hover` | #3B6FA8 / #2F5C8C | Buttons, links, progress, focus | white text 5.22 / 6.93 |
| `--color-primary-soft` | #EAF1F9 | Stat tiles, active nav pill, selected rows, info notices | primary-hover text 6.09 |
| `--color-success` on `-soft` | #1F7A55 on #E6F4EE | "Ready", success notices | 4.67 |
| `--color-warning` on `-soft` | #B45309 on #FDF1E3 | "Analysing" | 4.51 |
| `--color-danger` | #C2413B | Danger buttons, error text on white | 5.11 |
| `--color-danger-strong` on `-soft` | #AD3A34 on #FCEBEA | "Analysis failed", error notices | 5.31 (#C2413B was 4.43) |
| `--color-border` | #E2E8F0 | Panel outlines, row dividers (decorative) | |
| `--color-border-strong` | #8592A6 | Inputs, secondary buttons | 3.15 |

- The header is white with a 1px bottom border; the current page is a primary-soft pill. The logo keeps its own green (`--color-logo`), never used for UI.
- One main colour: primary blue. At most one filled primary button per view (the landing page may repeat "Log in" in its top bar).
- The interface never names the LGU, except the landing-page footer, which credits the partner office (DPWH Cavite 2nd District Engineering Office).
- Map class colours (`--damage-*`): D00 #0E9384 teal, D10 #D97706 amber, D20 #7C5CC4 violet, D40 #D64545 red, unknown #64748B. Route and control pins `--map-route` #1E293B. Graphics only, never text. A GPS dot has a 2px white halo; a hand-placed dot has a dashed class-colour stroke over a 35% fill.

Survey status labels (8px radius, icon plus text, 14px semibold):

| Status | Icon | Colours |
|---|---|---|
| Waiting to start | clock | muted on white, 1px border |
| Analysing n% | half-filled circle, plus blue progress bar | warning on warning-soft |
| Ready | check | success on success-soft |
| Analysis failed | alert circle | danger-strong on danger-soft |

Inspection statuses stay plain text. Confidence is plain "27%": no bar, colour or warning.

## 5. Type

Public Sans, weights 400, 600 and 700 only. Monospace is for code only (a raw error message). Use tabular figures (`.num`) on times, percentages, counts and coordinates.

| Token | Size | Line height | Weight | Use |
|---|---|---|---|---|
| `--text-sm` | 0.875rem | 1.45 | 400 / 600 | Hints, meta, small labels, footer. The floor. |
| `--text-base` | 1rem | 1.5 | 400, buttons 600 | Body, inputs, buttons |
| `--text-md` | 1.125rem | 1.4 | 600 | Panel titles |
| `--text-lg` | 1.375rem | 1.3 | 700 | Section headings, empty states |
| `--text-xl` | 1.75rem (1.5rem on phones) | 1.25 | 700 | Page title (h1) |
| `--text-stat` | 2.25rem | 1.1 | 700 | Overview counts only |

## 6. Space, size, shape

- Spacing on a 4px base: `--space-1` 0.25rem … `--space-8` 4rem.
- Page gutters 16px on phones, 32px on desktop. 32px between sections. Panel padding 24px (16px on phones).
- Content max width 72rem; forms 40rem; the damage map runs full width.
- Radius 8px for buttons, inputs and labels; 12px for panels, cards, menus, dialogs and popups. Only the active nav item is a pill.
- Borders: 1px `--color-border` around panels and between rows in lists and tables only. Inputs 1px `--color-border-strong`.
- Elevation: `--elevation-0` is a very soft shadow on cards and panels. `--elevation-1` only for floating things: menus, the dialog, map popups, the phone menu.
- The header collapses to a "Menu" button below 64rem.

## 7. Actions

All buttons are at least 44px tall, 8px radius, weight 600.

| Kind | Look | Examples |
|---|---|---|
| Primary | Filled blue, white text, one per view | Upload video, Save points and place damage |
| Secondary | White, ink text, 1px strong border | See on the map, Download, Show all surveys |
| Quiet | No border, blue text, subtle fill on hover | Reload, Clear filters, Rename, Cancel |
| Danger | Filled red | Only the confirm button in the delete dialog. In menus "Delete survey" is red text with a bin icon |
| Icon-only | 44x44 with `aria-label` | Only "More actions for <name>" and "Remove point <n>" |
| Link | Blue, underlined | Navigation inside text. Row titles are bold ink, underlined on hover and focus |

Disabled buttons always show the reason next to them.

## 8. Icons

About 30 hand-written inline SVG icons in `src/icons.jsx`, outline style (24px viewBox, 2px stroke, round caps, `currentColor`). No icon package.

- Always next to words. The only icon-only controls are "More actions" and "Remove point".
- `aria-hidden="true"` on every icon; 20px in buttons and nav, 16px in labels, 48px only in empty states.
- Never in the damage-class colours. Damage classes never get icons.
- Not on every fact in a row: only in status labels, action buttons, nav, notices, overview tiles and empty states.

## 9. Information architecture

- One white header: logo and "OcuLubak"; role-filtered nav (Overview, Upload, Surveys, Damage map, Damage records), current page as a primary-soft pill; account button opening a panel with the name, role, "About OcuLubak" and Sign out.
- Public landing page (`LandingPage.jsx`): "/" for visitors, "/about" for everyone; login is at "/login". Signed-in users get the Overview at "/".
- Survey detail and "Place on the map" are two tabs of one survey page (both URLs kept). The second tab appears only for surveys without GPS that did not fail.
- Survey list: the title opens the survey; one visible next-step button; everything else in a "More" menu.
- Menus use the disclosure pattern (button with `aria-expanded`, Escape and outside click close). Delete confirmation is a native `<dialog>`. Optional sections ("Add a GPS track", "How this works", phone "Filters") are native `<details>`.

## 10. Data display

Every number must trace to a column in the database. If you cannot name the column, delete the number.

- No invented metrics, composite scores or time-saved figures.
- Numbers carry their unit and their reference point.
- Counts are allowed to be small. Real and small beats impressive and fake.

## 11. Do not build

- Gradients, glass or blurred panels, glows
- Invented statistics or scores, "Powered by AI" labels
- Emoji anywhere in the interface
- Pill-shaped badges
- Amber or yellow outside the "Analysing" label and the D10 map colour
- Map class colours anywhere except the map
- A second filled button in the same view

## 12. States

Designed at the same time as the default view, not after.

- **Empty.** A 48px icon, a heading and one action. An invitation, not an apology.
- **Loading.** Skeleton rows matching real row height. No full-screen spinners.
- **Error.** Name what failed and what to do. Never "Something went wrong".

## 13. Quality floor

- Responsive from 360px up, with no horizontal page scroll.
- Visible keyboard focus: 3px primary outline, 2px offset.
- Text contrast 4.5:1 minimum; text never below 0.875rem; rem units.
- Tap targets 44px minimum.
- Motion limited to state transitions under 200ms. No entrance animations.
- Semantic HTML and a logical heading order on every page. A list is a list. A nav is a nav.
