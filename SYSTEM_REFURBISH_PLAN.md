# Bantay Kalsada — System Refurbishment & Demo Readiness Plan

**Do not touch during any phase of this plan:** thesis text, pseudocode,
formulas, figures. Chapter 3 gets rewritten only after this plan is complete
— see the separate `CHAPTER_3_UPDATE_CHECKLIST.md`.

---

## PART A — URGENT: Demo-Ready for Tomorrow's Software Engineering 2 Presentation

**Context:** No dataset exists yet. The four-class fine-tuned model does not
exist yet. This section is scoped to what's achievable in hours, using what
already works, without risking the system breaking right before a
presentation. Dataset collection and model training are NOT part of this
section — they stay on the thesis timeline in Part B.

### What to demo
The working end-to-end pipeline: video + GPS upload → frame extraction →
inference (using whatever model currently exists — it's fine and expected
that this is not yet the four-class local fine-tune) → detection display →
dashboard/map view. An SE2 audience is evaluating system engineering and
architecture, not final model accuracy — say this plainly if asked: "the
current model is a working baseline; the four-class fine-tune on local data
is in progress as part of Thesis 2."

### Safe to do today (low risk, no retraining required)
- [ ] **Class code correction** (Phase 1 from the full plan, below) — this is
      a rename/consistency pass across the codebase, not a retrain. Low risk,
      worth doing now so the demo shows the correct D00/D10/D20/D40 labeling
      convention instead of the old incorrect one.
- [ ] **Remove severity scoring remnants** (Phase 2, below) — also a
      removal/cleanup pass, not a retrain. Low risk.
- [ ] **Dry-run the full upload → detection → dashboard flow at least once**
      before presenting, end to end, on the actual machine/network you'll
      demo on.
- [ ] **Prepare a recorded screen-capture backup** of one successful full run,
      in case live demo hits a network/environment issue during presentation.

### Explicitly deferred past tomorrow (do NOT attempt tonight)
- [ ] Role model simplification (Phase 3) — touches login/auth/navigation
      logic; a partial migration attempted under time pressure is more likely
      to break the demo than improve it. Verbally mention it's planned if
      asked; don't rush the code change.
- [ ] Authentication rework (Phase 4) — same reasoning. Not needed for a
      demo to function.
- [ ] Any dataset/model work (Part B) — this cannot be done in hours
      regardless of urgency; don't attempt a rushed placeholder training run
      that could produce a broken or misleading model right before presenting.

**Bottom line for tonight:** two cheap, safe correctness fixes (class codes,
severity removal), one rehearsal run, one backup recording. Nothing else.

---

## PART B — Full Thesis System Refurbishment (ongoing, no fixed deadline)

### 0. Ground rules
- Class scheme: `D00` (longitudinal), `D10` (transverse), `D20` (alligator),
  `D40` (pothole). No `D30`.
- Two roles only, eventually: Road Maintenance Personnel, System
  Administrator. Current four-tier role set gets collapsed — deferred past
  the SE2 demo per Part A.
- No severity scoring, anywhere.
- Auth needs to be real enough that the paper's claims stop being false,
  without becoming a production security project.
- **80% mAP@50 is a stated target, not a guarantee this plan can promise.**
  Confirm with your adviser whether it's a hard pass/fail gate or whether a
  documented, root-cause-analyzed shortfall is acceptable — before investing
  heavily in the harder mAP-boosting techniques in Phase 6.

---

### Phase 1 — Class Scheme Correction
*(Same scope as before — do this first, it's also part of Part A.)*
- [ ] Audit `backend/models.py`, `backend/migrate.py`, `ml/` training config,
      backend routes, and `frontend/src/` for class labels/mappings.
- [ ] Search repo-wide for the literal string `D30`; confirm every hit is
      removed or was already correct.
- [ ] Confirm the RDD2022 filtered subset uses the correct four codes.

### Phase 2 — Remove Severity Scoring
*(Same scope as before — also part of Part A.)*
- [ ] Search backend models, routes, frontend pages, and export/report
      generation for any severity-related fields or UI.
- [ ] Confirm no training/inference code computes a severity score.

### Phase 3 — Role Model Simplification (four roles → two)
*(Deferred past the SE2 demo — do this once there's no presentation risk.)*
- [ ] Decide the mapping explicitly before writing code: recommend flattening
      `barangay/municipal/provincial` fully into "Road Maintenance
      Personnel," not preserving internal tiers.
- [ ] Update role enum in `backend/models.py`, migration logic in
      `backend/migrate.py`, route enforcement, frontend nav guards, and
      default-admin-account creation.

### Phase 4 — Authentication Fix (minimal real JWT)
*(Deferred past the SE2 demo.)*
- [ ] Add a JWT library (e.g. `PyJWT`), issue signed tokens with expiry on
      login, verify signature + expiry on every protected route.
- [ ] Skip refresh tokens/revocation lists — document as a scoped
      simplification, the same way SQLite's concurrency limits are disclosed.
- [ ] Update frontend API client to store/attach the token and handle 401s.

### Phase 5 — Dataset Preparation Pipeline

**Primary (local) dataset:**
- [ ] Target: **1,500 frames stretch goal, 500–800 frames fallback** if 1,500
      isn't feasible — document whichever number is actually hit, and the
      reason, in the methodology. Confirm the final number with your adviser
      before treating it as locked.
- [ ] Capture via the three team members' dashcams across different road
      segments (national/city/barangay) and lighting conditions, in parallel
      rather than sequentially.
- [ ] Confirm GPS logging capability per dashcam (built-in or companion app);
      if unavailable, run a separate phone GPS-logger app per drive,
      timestamped against the dashcam clock.
- [ ] Extract candidate frames from footage programmatically (reuse/adapt the
      frame-extraction logic already in `video_processor.py` rather than
      building a separate script).
- [ ] **Bootstrap labeling order:** train the RDD2022-only baseline first
      (Phase 6 depends on this anyway) → use that model to generate draft
      detections on local frames (model-assisted pre-labeling in Roboflow or
      CVAT) → team corrects predictions rather than labeling from scratch →
      this is materially faster than manual-from-zero annotation.
- [ ] Draft a shared labeling rubric before annotation starts, so all three
      team members label consistently.
- [ ] Run a calibration session with the DPWH contact early (small shared
      sample, compare labels, resolve disagreements into a clearer rubric).
- [ ] **Stratified QA sample:** group final annotated frames by damage class,
      randomly sample ~10-15% from each class group (not from the pool as a
      whole), send that stratified sample to the DPWH contact for spot-check
      verification, and record the agreement rate as a reportable
      data-quality metric.

**Secondary (foreign) dataset:**
- [ ] Use the **India** subset of RDD2022 (9,665 images) as the primary
      foreign source — write an explicit justification paragraph (climate,
      road-maintenance practice, traffic mix) rather than asserting
      similarity without support.
- [ ] Filter to the four corrected classes (`D00/D10/D20/D40`).

**Merge:**
- [ ] Combine local + India-subset data, keep source-tagged (local vs.
      foreign) for the later separate-subset evaluation your objectives
      already commit to.
- [ ] Split 70/20/10 (train/val/test), record absolute counts per class per
      split, not just percentages.

### Phase 6 — Model Training & Evaluation

- [ ] Confirm training config uses corrected 4-class mapping (must happen
      after Phase 1).
- [ ] Train the RDD2022(India)-only baseline first — this both gives you a
      real number to report and becomes the pre-labeling model for Phase 5.
- [ ] Fine-tune on the merged local+foreign dataset.
- [ ] Evaluate and report mAP@50, precision, recall, F1 **separately** for
      the foreign test subset and the local test subset, plus **per-class**
      breakdowns for each — this is what your defense strategy depends on if
      the aggregate falls short of 80%.

**If short of 80% after the first full training run, apply in this order:**
- [ ] Accessible tier: class-weighted loss / targeted oversampling of the
      weakest class, confusion-matrix-driven error analysis, hyperparameter
      sweep (learning rate, epochs, batch size, input resolution), an
      annotation-quality review pass.
- [ ] Confirm with adviser before attempting the harder tier: attention-module
      architecture changes, or switching model size (e.g. YOLOv8l) — both
      change what the methodology chapter claims the model is, and need
      sign-off first.
- [ ] Regardless of outcome, keep the per-class / per-subset results table —
      it's the input to Chapter 3's results discussion either way.

### Phase 7 — Regression Pass
- [ ] End-to-end test: upload video + GPS, confirm correct class labels,
      correct role-based access, auth flow (once Phase 4 lands).
- [ ] Confirm no dead code references removed severity feature or old
      four-tier roles.
- [ ] Confirm georeferencing modes (`gps_file`/`georeferenced`/`none`) still
      work — not touched by this plan, shouldn't be accidentally broken.

---

## Reminders (paper-side, not code)
- [ ] Add georeferencing feature description to methodology.
- [ ] Add operational limitations to Scope and Limitations: 10-minute video
      cap, thread-based processing risk on backend restart, `ffmpeg`
      dependency.
- [ ] Once Phase 4 is resolved, make the Ethics/Privacy JWT claim match
      whatever was actually implemented.
- [ ] Write the India-subset justification paragraph (climate/infrastructure
      similarity argument) for the secondary dataset section.
- [ ] Document the stratified QA sampling method and resulting agreement
      rate in the methodology once Phase 5 QA is complete.

---

## Definition of Done (gate before Chapter 3 rewrite starts)
All of Phase 1-7 complete, verified, both reminders done, and real per-class/
per-subset training numbers in hand. Only then move to
`CHAPTER_3_UPDATE_CHECKLIST.md`.
