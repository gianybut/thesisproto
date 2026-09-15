# design.md

## 1. Product context

A web application for local road maintenance staff to find and locate road damage without watching hours of survey video.

The user uploads a dashcam or road survey video. The system analyses it and returns a map showing where potholes and cracks were found.

Primary users are engineers and maintenance personnel at a municipal engineering office. They are not developers and they are not data scientists.

Most sessions are one task: upload a video, wait, look at the map, export the list. Sessions happen on a desktop in an office, occasionally on a phone in the field.

The value is that a two-hour survey becomes a located list in minutes. Nothing about the interface should require understanding how the detection model works.

## 2. Voice

Plain, specific, calm. Write like a competent friend, not like a marketing page.

- Name real things. Real places, real times, real prices.
- Say what happens, not how it feels.
- Buttons name their outcome. Never "Get started" or "Learn more".
- No hype adjectives: seamless, powerful, intelligent, effortless, revolutionary, premium.
- Sentence case everywhere, including buttons and headings.
- Copy test: if a sentence could be pasted onto a competitor's site unedited, rewrite it.

## 3. Color

| Token | Value | Use |
|---|---|---|
| `--paper` | `#F6F4EE` | Page background |
| `--card` | `#FFFDF8` | Raised panels, one step lighter than paper |
| `--ink` | `#1A1D19` | Primary text |
| `--ink-soft` | `#5C635A` | Secondary text, labels, metadata |
| `--cyan` | `#0E5661` | Primary action and active state only |
| `--rule` | `#DEDACE` | All borders and dividers, 1px |
| `--alert` | `#9C4A21` | Time-critical only, never decorative |

- Seven values. Do not add an eighth.
- `--cyan` appears at most twice per screen.
- No gradients anywhere. Not on backgrounds, text, buttons, or icons.
- No colored surfaces behind icons.
- Depth comes from a 1px `--rule` border, not from shadows.

## 4. Type

Display: Newsreader (400, 500, italic). Body: Archivo (400, 500, 600). Utility: IBM Plex Mono (400, 500). All three are on Google Fonts.

| Role | Size | Face | Notes |
|---|---|---|---|
| Page h1 | 60px / 1.07 | Newsreader 400 | letter-spacing -0.02em |
| Section h2 | 42px / 1.12 | Newsreader 400 | |
| Subhead h3 | 21px / 1.3 | Newsreader 500 | |
| Lede | 16px / 1.65 | Archivo 400 | max-width 460px |
| Body | 15px / 1.65 | Archivo 400 | |
| Secondary | 13 to 14px | Archivo 400 | uses `--ink-soft` |
| Eyebrow, label | 11 to 12px | Plex Mono 400 | uppercase, tracking 0.1em |
| Data, time, count | 12px | Plex Mono 400 | |

- Mono carries anything a machine produced. If a number came from data, it is set in mono. This one rule does more work than the rest of the file.
- Italic Newsreader is the emphasis device, used once per page at most.
- Measure caps around 70 characters. Never center a paragraph.

## 5. Layout

- 8px spacing base. Section rhythm runs 30 / 40 / 56px.
- Radius is 4px on buttons and 6px on panels. Nothing is pill-shaped except a real toggle.
- Asymmetric by default. A centered layout has to earn it, and it only earns it when there is genuinely nothing to place beside the text.
- Sections separate with a 1px rule, not with a background color change.
- Hero: text left, something real on the right, roughly 1.05 to 0.95.

## 6. Components

- **Buttons.** One primary per page, solid `--cyan`, 4px radius. Everything else is a text link. No outlined secondary button next to the primary one.
- **Cards.** A card is a bounded, tappable object that leads somewhere. If it is not tappable it is not a card, so use a divider instead.
- **Lists.** The default layout device. Rows separated by 1px rules, with mono in a fixed-width first column so numbers align down the page.
- **Icons.** Only where they replace a word. No icon in a colored square. No icon as decoration beside a heading.

## 7. Data display

Every number must trace to a column in the database. If you cannot name the column, delete the number.

- No invented metrics. No composite scores, no percentage improvements, no time-saved figures.
- Numbers carry their unit and their reference point.
- A chart appears only when the shape of the data is the point.
- Counts are allowed to be small. Real and small beats impressive and fake.

## 8. Do not build

Direct ban list. If the generated page contains any of these it is wrong, regardless of how it looks.

- Gradient backgrounds, text, or buttons
- Invented statistics or scores
- Glass or blurred translucent panels
- "Powered by AI" labels of any kind
- Emoji anywhere in the interface
- Streaks, levels, points, achievements
- Rows of three equal-weight cards
- Upgrade banners in the main flow
- Sparkle, rocket, lightning, fire icons
- Dark radial glow behind the hero
- Badge pills for status or category
- Centered hero with two side-by-side CTAs

## 9. States

Designed at the same time as the default view, not after.

- **Empty.** An invitation to act, not an apology.
- **Loading.** Skeleton rows matching real row height. No full-screen spinners.
- **Error.** Name what failed and what to do. Not "Something went wrong".

## 10. Quality floor

- Responsive from 360px up.
- Visible keyboard focus, 2px `--cyan` outline with 2px offset.
- Body text contrast 4.5:1 minimum.
- Tap targets 44px minimum.
- Motion limited to state transitions under 200ms. No entrance animations.
- Semantic HTML. A list is a list. A nav is a nav.
