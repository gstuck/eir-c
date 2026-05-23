# CHANGES.md — what I did, decisions I made

Status: everything ran. All 11 verification checks passed. Re-running the
generator produces byte-identical output, so the GitHub Action's
"commit only on change" logic will work correctly. PLAN.md describes my
reasoning before I started; this file describes what actually happened.

## What's in this folder

```
cwc-c-rev6/
├── .github/workflows/build.yml       Version A's GitHub Action (unchanged)
├── README.md                         Updated operating manual
├── PLAN.md                           My reasoning before starting
├── CHANGES.md                        This file
├── generate_pages.py                 NEW build script — Version A's
│                                       pipeline architecture, Version C's
│                                       templating throughout
├── convos.xlsx                       Version A's spreadsheet (unchanged)
├── styles.css                        Version C revision 5 stylesheet
├── about.html                        Version C styling, "reference lesson"
├── tips.html                         Version C styling, "reference lesson"
├── index.html                        Generated
├── 12 detail pages.html              Generated
└── pdfs/                             Version A's PDFs (unchanged)
    ├── 12 convo PDFs
    └── sparks/                       5 spark PDFs
```

## What I built

A new `generate_pages.py` that has the same architecture as Version A —
`load_convos()` reads the spreadsheet, then `render_detail_page()` and
`render_index()` build HTML files — but produces Version C styled output.
The script is ~600 lines and structurally mirrors Version A's so anyone
who already knows the V.A build pipeline will find this familiar.

The build pipeline (spreadsheet → script → GitHub Action → live site)
works exactly like Version A. The only difference is what comes out the
other end.

## Decisions I made without asking (full list)

I made these calls because we'd already established the answers earlier
in the conversation, or because asking would have meant stopping.

### From PLAN.md (decided before starting)

1. **anatomy.html dropped.** Version A had a third nav item "Anatomy of a
   Convo." Version C never had this page and you never mentioned it.
   The two-banner index ("What's in each convo" + "Can I get the reference
   lessons") covers what anatomy.html did. If you want anatomy.html back,
   the file exists in the original Version A zip — copy it across, restyle
   to match the new about/tips pages, and add it to the nav in
   `SITE_HEADER` (in generate_pages.py) and in about.html / tips.html.

2. **Nav uses Version C labels** — "About the Convos / Tips for a Great
   Convo." Cleaner two-item nav than Version A's three-item one.

3. **"Focus Lesson" column names in the spreadsheet kept as-is.** Renaming
   them would force you to also update the spreadsheet. The script reads
   from those columns but labels the rendered UI as "reference lesson."
   If you want the column names changed later, search `generate_pages.py`
   for "Focus Lesson Name" and "Focus Lesson URL" — two edits.

4. **Hero stat cards on the homepage went from 4 to 3.** Version A had
   Topics / Min / Participants / Prep. Version C has minutes / educators /
   prep. The dynamic Topics count is dropped — it's implicit in the cards
   below. If you want it back, edit `render_index()` to insert a stat
   card with `n_topics = len(convos)`.

5. **Three themes, all of them.** The earlier hand-built Version C
   index.html showed only 2 themes (Deepening + Discourse) — I'm reading
   that as an unfinished state, since the spreadsheet has 3 themes and
   THEME_ORDER in the generator lists all 3. If you actually wanted
   Real World hidden for some reason, the easy fix is to remove
   "Focusing on the Real World" from THEME_ORDER and drop those convos
   from the spreadsheet.

6. **Placeholder convo #12 "Short Title" stays in.** It's in the
   spreadsheet, the original Version A includes it, and the spreadsheet
   workflow expects this kind of placeholder for demo purposes. Delete
   the row from convos.xlsx if you don't want it.

### Discovered while building

7. **`short-title.html` renders as a video page, not a PDF page.** The
   placeholder #12 row has Spark Type = "PDF" but Spark URL =
   `https://vimeo.com/1191661894`. The script (mirroring Version A) decides
   video-vs-PDF based on whether the URL parses as Vimeo. So the page gets
   the video modal. Version A behaves the same way. Either fix is fine:
   clear the Spark URL to match the type, or change the type to "Animated
   Video" to match the URL. Or just delete the row.

8. **Indentation in generated HTML differs slightly from the hand-built
   Version C complex-problems.html I made earlier.** Only whitespace —
   tag skeleton is identical (I diff-checked). Browsers don't care.
   Diffs will be slightly noisy on first commit but stable thereafter.

9. **The "Preview the reference lesson" button is conditional.** If a
   row has no Focus Lesson URL, that button is omitted rather than rendered
   as a broken link. The original Version A always rendered it (with
   whatever the cell contained, potentially blank). Version C is slightly
   more careful here.

## Things I kept the same as Version A

These are deliberate retentions, called out in case you want to change
them later:

- **`LOCKED_SLUGS` dict** — convos #1-11 keep their slugs even if the
  Short Title changes. Renaming a slug = edit this dict + rename PDFs.
- **`THEME_ORDER` list** — homepage theme order. Hardcoded.
- **`THEME_LESSONS` dict** — the "Real-World Math lesson used for Spark:
  X by Citizen Math" callout under each theme header. The third theme
  ("Focusing on the Real World") has THREE lessons: Big Foot Conspiracy,
  Seeking Shelter, Coupon Clipping. Hardcoded — not pulled from the
  spreadsheet.
- **Mailto button body text** — same template as Version A.
- **PDF path conventions** — `pdfs/{slug}.pdf` for convo guides,
  `pdfs/sparks/{slug}-spark.pdf` for sparks.
- **Vimeo embed parameters** — same query string as Version A
  (autoplay, no title, etc.).
- **`vumbnail.com/{id}.jpg` thumbnail** for video sparks. If vumbnail
  goes away, swap this URL.
- **GitHub Action workflow file** — same, but pointed at the new script.

## Verification I ran

1. ✅ Generator runs cleanly on the bundled spreadsheet. No errors.
2. ✅ No NaN / None / unfilled template placeholders in any output.
3. ✅ No "focus lesson" anywhere — all 15 HTML files cleaned.
4. ✅ Index has all 3 themes, 12 cards, 3 carousels.
5. ✅ Every detail page has all 4 section-num circles (Observe=1,
   Discuss=2, Relate=3, Commit=4).
6. ✅ Each detail page links to the right `pdfs/{slug}.pdf`.
7. ✅ PDF spark pages link to spark PDFs that exist on disk.
8. ✅ Video modal markup ONLY on pages with video sparks.
9. ✅ styles.css has all the role-based palette and new rules.
10. ✅ .github/workflows/build.yml present.
11. ✅ about.html and tips.html use the new Corben/Inter typography.
12. ✅ Generator is deterministic — running twice produces identical
    bytes, so the Action won't commit empty diffs.

## How the GitHub Action will behave on first upload

When you upload this folder to your `eir` repo, the Action will trigger
(because convos.xlsx + build.yml + generate_pages.py all changed). It will:

1. Check out the repo.
2. Run `python generate_pages.py`.
3. Diff *.html against what's now in the repo.
4. Find no diff (because what you uploaded matches what the script
   produces).
5. Print "No HTML changes — nothing to commit" and exit clean.

If you ever edit the spreadsheet and re-upload, the Action will run
again. This time it WILL find a diff (because the script's output
differs from the previous HTML), commit those changes as "convo-bot,"
and push.

## How to verify the site locally before deploying

```bash
cd cwc-c-rev6
python3 -m http.server 8000
# Open http://localhost:8000 in a browser
```

This serves the folder. The PDFs work as relative links from there.

## What to do tomorrow if anything's off

- **Generator misbehaving?** Try `CWC_OUTPUT_DIR=/tmp/test python3
  generate_pages.py` to run it without touching anything you care about.
- **Want to add a new theme?** Add it to THEME_ORDER in the script, give
  it an entry in THEME_LESSONS, and put a matching value in the
  spreadsheet's Theme column.
- **Want to rename a slug?** Edit LOCKED_SLUGS *and* rename the PDF in
  `/pdfs/{old}.pdf` to `/pdfs/{new}.pdf` *and* rename the spark in
  `/pdfs/sparks/`. The script doesn't do the PDF renames; you do.
- **Want to drop the `short-title` placeholder convo?** Delete row 12
  from convos.xlsx and re-upload. The script will regenerate without it
  and the orphan `short-title.html` will linger in the repo until you
  delete it manually.

If something's seriously wrong, the original Version A zip is still in
`/mnt/user-data/uploads/eir-main.zip` and the older Version C files are in
`/mnt/user-data/outputs/cwc-c-rev5/`. Both can be restored without losing
the work in this folder.
