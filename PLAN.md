# Plan: port Version A's build pipeline to Version C's styling

This is the reasoning behind the refactor. The CHANGES.md (written when the
work is done) is the result. Read this first if anything looks surprising.

## What I'm doing

Version A has a build pipeline that generates HTML from a spreadsheet plus
PDFs on disk. Version C (which we've been riffing on in this conversation) is
a hand-built site with a more deliberate visual style — six-role palette,
two-column hero, numbered phase circles, dot-pattern atmosphere, etc.

The goal: keep Version A's pipeline (spreadsheet + PDFs + GitHub Action) but
make the generated output match the Version C styling we've been building.

## What stays from Version A

- `generate_pages.py` — the script architecture: `load_convos()`, `slugify()`,
  `render_detail_page()`, `render_index()`, `main()` orchestration.
- The spreadsheet schema (column names, sheet name, header row 1 0-indexed).
- `LOCKED_SLUGS` — locks URLs for the 11 original convos so PDFs stay linked.
- `THEME_ORDER` and `THEME_LESSONS` — homepage theme ordering + lesson
  callouts (still hardcoded since they're not in the spreadsheet).
- The PDF naming convention: `pdfs/{slug}.pdf` for the merged guide,
  `pdfs/sparks/{slug}-spark.pdf` for the standalone spark.
- The GitHub Action (`.github/workflows/build.yml`).
- The "auto-commit only on change" behavior.

## What changes — output template only

These all come from the Version C work we did in earlier turns:

1. **Font stack: Corben + Inter + Caveat** (Version A used Lora + Inter).
   The Google Fonts link in every generated page now requests Corben & Caveat.
2. **Stylesheet is the Version C revision 5 stylesheet** I built earlier in
   this conversation, with role-based palette + honey amber replacing olive.
3. **Header markup matches Version C** — a smaller, simpler site-header with
   only About + Tips in the nav. (Version A also had `anatomy.html` but since
   Version C never had that page and the user hasn't asked for it, I'm not
   adding it back; see the "anatomy.html" decision below.)
4. **Footer matches Version C** — the chair-pulling-up animation, the Caveat
   CTA list ("invite your colleagues / print the convo guides / pull up a
   chair"), and the footer tagline.
5. **Detail-hero is two-column** — content left, prep-zone (action buttons)
   right. Stacks below 800px.
6. **No "Use Online Convo Guide" button or modal.** User explicitly asked to
   remove this in the previous round.
7. **Phase numbered circles** in each section header (Observe=1, Discuss=2,
   Relate=3, Commit=4), colored peach / honey / dark-teal / mahogany.
8. **Question bullets are colored dots**, not numbers, picking up the phase
   color.
9. **"Focus lesson" → "Reference lesson"** everywhere in generated output.
   The spreadsheet's column is still "Focus Lesson Name" / "Focus Lesson URL"
   — we don't rewrite that. The generator just renders the value with the
   new label in the UI.
10. **Index hero uses the Version C structure** — eyebrow + h1 + dek on the
    left, no "what's in each convo" callout in the hero (that lives in a
    dark-slate banner farther down the page in Version C). Plus the
    three colored stat cards (mahogany / peach / dark-teal in Version C; I'm
    preserving that color rotation).
11. **Index has the two banners** from Version C — the dark "What's in each
    convo" banner and the burnt-peach "Can I get the reference lessons for
    myself?" banner.
12. **Convo cards on the homepage use Version C styling** — the carousel
    with optional arrows when content overflows. (Version A used a plain
    `.convo-grid`; Version C uses a `.convo-shelf` with adaptive arrows and
    fade overlays. I'm porting the shelf structure into the generator, plus
    the inline `<script>` that drives the adaptive arrow visibility.)

## Decisions I'm making without asking

These came up in implementation. I picked the most sensible option and
documented it.

### anatomy.html
Version A had a hand-edited `anatomy.html` page in the nav ("About / Anatomy
of a Convo / Tips"). Version C does not have this file or this nav item;
its nav is "About the Convos / Tips for a Great Convo". The user hasn't
mentioned anatomy.html during our Version C work. I'm preserving Version C's
two-item nav and **not** copying anatomy.html across. If you want it back,
it would slot in as a third nav item between the existing two, and the file
exists in the Version A zip if you want to copy it manually.

### Nav labels
Version A: "About / Anatomy of a Convo / Tips for a Great Convo"
Version C: "About the Convos / Tips for a Great Convo"
Going with Version C's labels.

### Spark Type matching
The script branches on whether `Spark URL` is a Vimeo URL (→ video spark)
or anything else (→ PDF spark — reads from `pdfs/sparks/{slug}-spark.pdf`).
Version A keeps this logic; I keep it identically. The `Spark Type` column
in the spreadsheet is informational only — the actual branch is on whether
a Vimeo ID can be parsed out of `Spark URL`.

### Index theme groupings + ordering
Version A groups cards into 3 themes via `THEME_ORDER`. I'm preserving that
behavior. Version C originally had only 2 themes shown in the hand-built
index.html, but the user clearly intends the full 3-theme structure (the
prior `index.html` shows it'd been edited down for some demo reason; the
spreadsheet has all 3 themes). I'm going with the spreadsheet.

### Index — "Focusing on the Real World" lesson callout
Version A puts THREE lessons under this theme (Big Foot Conspiracy, Seeking
Shelter, Coupon Clipping). Version C's hand-built index only shows two
themes (Deepening + Discourse), so I never saw a version-C-styled
3-lesson callout. I'm preserving Version A's THEME_LESSONS dict as-is.

### "Focus Lesson" column name in spreadsheet
The spreadsheet still says "Focus Lesson Name" and "Focus Lesson URL". I'm
leaving the column names alone — renaming them would force the user to also
rename in the spreadsheet, which is invasive. The generator reads from
those columns and emits "reference lesson" labels in the UI. If the user
wants to rename the columns later, it's a one-line edit in the script.

### Hero meta strip on detail pages
Version A and Version C both have a dark teal strip above the detail hero
("30-60 min · 2-5 educators · no facilitator needed"). I'm keeping it.

### Stat cards on homepage
Version A: 4 stat cards (Topics count, 30-60 Min, 2-5 Participants, 0 Prep)
Version C: 3 stat cards (30-60 minutes, 2-5 educators, 0 prep)
Going with Version C's three cards — they have more descriptive labels and
the colors (mahogany / peach / dark teal) read like a curated palette
rather than a sports scoreboard. The dynamic "Topics" count is lost; I'm
fine with that since the count appears implicitly via the 11+ cards below.

### The "Short Title" convo (placeholder #12 in spreadsheet)
The current spreadsheet has 12 rows where #12 is the example "Short Title"
placeholder. Version A's index includes it. My generator should too — it's
not my place to filter it out, and the spreadsheet workflow expects exactly
this kind of placeholder for demo purposes. If the user wants it gone they
can delete the row from the spreadsheet.

## File layout the user should expect

After this runs, `/mnt/user-data/outputs/cwc-c-rev6/` contains:

```
cwc-c-rev6/
├── .github/workflows/build.yml      # the GitHub Action
├── README.md                        # updated operating manual
├── PLAN.md                          # this file
├── CHANGES.md                       # what I did, written after
├── generate_pages.py                # NEW — Version C templating
├── convos.xlsx                      # copied from Version A
├── styles.css                       # Version C rev 5 stylesheet
├── about.html                       # Version C, "reference lesson" swept
├── tips.html                        # Version C, "reference lesson" swept
├── index.html                       # generated
├── (12 detail pages).html           # generated
└── pdfs/                            # copied from Version A
    ├── (11 + 1 placeholder PDFs)
    └── sparks/
        └── (PDF sparks)
```

The user should be able to upload this whole folder to the repo and have
everything work — including triggering the Action manually after the upload
to confirm the build is reproducible.

## Verification I'll run before declaring done

1. The script runs cleanly with `python generate_pages.py` against the bundled
   spreadsheet and produces 12 detail pages + 1 index without errors.
2. The output HTML files validate by quick inspection — no broken templates,
   no NaN-leaking-into-output (the `safe()` helper from Version A handles
   this), no obvious empty `<p>` tags or "None"s.
3. A diff between a generated page and the Version-C-styled `complex-problems.html`
   from earlier in this conversation should be small — same skeleton, same
   classes, same nav, same footer. Differences should only be: the spark
   block details (because different convos have different sparks), the
   convo-specific text content, and the URLs in the prep-zone buttons.
4. The index page rendered should have all 3 themes, correct theme-lesson
   callouts, and 12 cards spread across them.
5. No leftover references to "focus lesson" in any generated HTML file.
6. The convo-shelf adaptive-arrow script is included in the generated index.

## Testing the round-trip
After the build, I'll re-run the build a second time. The Action's "commit
only on change" logic depends on this being deterministic — second run
should produce identical bytes.
