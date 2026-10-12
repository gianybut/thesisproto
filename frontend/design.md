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

1. One main action per screen: at most one filled green button per view.
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

| Token | Hex | Use | Contrast |
|---|---|---|---|
| `--color-header` | #13294B | Navy header bar, phone menu panel | white text 14.52 |
| `--color-header-muted` | #C5D0E0 | Role, inactive nav on navy | 9.31 on navy |
| `--color-bg` / `--color-surface` | #FFFFFF | Page, panels, inputs | |
| `--color-subtle` | #F5F6F3 | Count tiles, table heads, skeletons, hover fills, footer | ink 15.38, muted 7.15 |
| `--color-ink` | #17201B | Body text, headings | 16.68 on white |
| `--color-muted` | #4A5550 | Hints, meta lines | 7.76 on white |
| `--color-primary` | #046B3E | Logo green: primary buttons, links | 6.61 |
| `--color-primary-hover` | #03552F | Primary hover | 8.96 |
| `--color-primary-tint` / `-strong` | #E5F1EA / #035230 | "Ready", success notices, selected rows | 8.03 |
| `--color-danger` | #A1262B | Delete, error text | 7.43 |
| `--color-danger-tint` / `-strong` | #FBECEC / #8E1F24 | "Analysis failed", error summary | 7.72 |
| `--color-border` | #D3D9D4 | Panel outlines, row dividers (decorative) | 1.43 |
| `--color-border-strong` | #7A847E | Inputs, secondary buttons | 3.87 |
| `--color-focus` | #17201B | 3px outline, 2px offset | |
| `--color-focus-on-header` | #FFFFFF | Focus ring and current-page underline in the header | |

- No amber or yellow anywhere. Pothole #D55E00 stays unique to the map.
- The logo green is 2.2:1 on navy, so in the header the logo sits on a 40px white tile.
- Navy appears only in the header, the phone menu, and chrome drawn on maps (route line, control-point pins).
- The footer is light grey with a 1px top border.
- The interface never names the LGU (no "Local Government Unit of Mendez-Nuñez, Cavite" in the header, footer, login or page metadata).
- Map class colours: D00 #009E73, D10 #0072B2, D20 #CC79A7, D40 #D55E00, unknown #5C635A. They pass 3:1 for graphics and are never used as text. A GPS dot has a 2px white halo; a hand-placed dot has a dashed class-colour stroke over a 35% fill.

Survey status labels (4px radius, icon plus text, 14px semibold):

| Status | Icon | Colours |
|---|---|---|
| Waiting to start | clock | muted on white, 1px border |
| Analysing n% | half-filled circle, plus green progress bar | ink on subtle |
| Ready | check | primary-strong on primary-tint |
| Analysis failed | alert circle | danger-strong on danger-tint |

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
- Radius 4px for buttons, inputs and labels; 8px for panels, menus, dialogs and popups. No pills.
- Borders: 1px `--color-border` around panels and between rows in lists and tables only. Inputs 1px `--color-border-strong`.
- Elevation: level 0 is flat. Level 1 (`--elevation-1`) only for floating things: menus, the dialog, map popups, the phone menu.
- The header collapses to a "Menu" button below 64rem.

## 7. Actions

All buttons are at least 44px tall, 4px radius, weight 600.

| Kind | Look | Examples |
|---|---|---|
| Primary | Filled green, white text, one per view | Upload video, Save points and place damage |
| Secondary | White, ink text, 1px strong border | See on the map, Download, Show all surveys |
| Quiet | No border, green text, subtle fill on hover | Reload, Clear filters, Rename, Cancel |
| Danger | Filled red | Only the confirm button in the delete dialog. In menus "Delete survey" is red text with a bin icon |
| Icon-only | 44x44 with `aria-label` | Only "More actions for <name>" and "Remove point <n>" |
| Link | Green, underlined | Navigation inside text. Row titles are bold ink, underlined on hover and focus |

Disabled buttons always show the reason next to them.

## 8. Icons

About 30 hand-written inline SVG icons in `src/icons.jsx`, outline style (24px viewBox, 2px stroke, round caps, `currentColor`). No icon package.

- Always next to words. The only icon-only controls are "More actions" and "Remove point".
- `aria-hidden="true"` on every icon; 20px in buttons and nav, 16px in labels, 48px only in empty states.
- Never in the damage-class colours. Damage classes never get icons.
- Not on every fact in a row: only in status labels, action buttons, nav, notices, overview tiles and empty states.

## 9. Information architecture

- One navy header: logo tile and "OcuLubak"; role-filtered nav (Overview, Upload, Surveys, Damage map, Damage records), current page white with a 3px underline; account button opening a panel with the name, role and Sign out.
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
- Marketing heroes; amber or yellow
- Map class colours anywhere except the map
- A second filled button in the same view

## 12. States

Designed at the same time as the default view, not after.

- **Empty.** A 48px icon, a heading and one action. An invitation, not an apology.
- **Loading.** Skeleton rows matching real row height. No full-screen spinners.
- **Error.** Name what failed and what to do. Never "Something went wrong".

## 13. Quality floor

- Responsive from 360px up, with no horizontal page scroll.
- Visible keyboard focus: 3px outline, 2px offset (white inside the header).
- Text contrast 4.5:1 minimum; text never below 0.875rem; rem units.
- Tap targets 44px minimum.
- Motion limited to state transitions under 200ms. No entrance animations.
- Semantic HTML and a logical heading order on every page. A list is a list. A nav is a nav.
