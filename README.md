# Convos with Colleagues — site package

Everything you need to:

1. Run the live site with the new Version C styling.
2. Update content by editing the spreadsheet — no code changes.

Goal: upload this folder once to your `eir` repo and walk away. Going
forward, edit `convos.xlsx` and the site updates itself.

## What's in this folder

```
cwc-c-rev6/
├── about.html                  Hand-edited About page
├── tips.html                   Hand-edited Tips page
├── index.html                  Auto-generated from spreadsheet
├── 12 convo detail pages.html  Auto-generated from spreadsheet
├── styles.css                  Version C stylesheet
├── generate_pages.py           The build script (used by the Action)
├── convos.xlsx                 The spreadsheet (source of truth)
├── pdfs/                       PDFs (Convo Guides + Sparks)
├── .github/workflows/
│   └── build.yml               The GitHub Action
├── README.md                   This file
├── PLAN.md                     My reasoning (overnight build session)
└── CHANGES.md                  What I decided + verification notes
```

Everything should end up in your `eir` repo. The folder structure matters
— `.github/workflows/build.yml` needs to live in those exact subfolders,
not at the root.

## The upload (10 minutes, all at once)

### Step 1: Upload the regular files

1. Open this folder on your computer.
2. Go to your `eir` repo on GitHub.
3. Click **"Add file" → "Upload files."**
4. Select all the files except the `.github` folder — all the `.html`,
   `.css`, `.py`, `.xlsx`, and `.md` files, plus the entire `pdfs/`
   folder — and drag them onto the upload area.
5. Wait for the uploads to finish.
6. Scroll to "Commit changes." Leave the defaults. Click
   **"Commit changes."**

GitHub will overwrite the existing files with these new versions. Your
live site will update within 1-2 minutes.

### Step 2: Add (or update) the GitHub Action

The `.github/workflows/build.yml` file lives in a subfolder, which makes
drag-and-drop awkward. Easier to create or edit it directly in the
GitHub UI.

1. If `.github/workflows/build.yml` already exists in your repo (you set
   it up previously with Version A), open it and update its contents from
   this folder's `build.yml`. Otherwise:
2. In your repo, click **"Add file" → "Create new file."**
3. In the filename box, type exactly: `.github/workflows/build.yml`
4. Open `.github/workflows/build.yml` from this folder in any text editor.
5. Select all, copy. Paste into the GitHub editor.
6. Scroll down. Click **"Commit changes."**

### Step 3: Watch the Action run

1. In your repo, click the **"Actions"** tab.
2. You'll see a workflow run for "Regenerate site pages from spreadsheet."
3. If it doesn't run automatically, click into the workflow name in the
   sidebar and click **"Run workflow"** in the top right.
4. The first run should say "Loaded 12 convos" and either "No HTML
   changes" (most likely, since the uploaded pages already match the
   script's output) or commit a small whitespace cleanup.

That's the whole setup.

## Your ongoing editing workflow

Whenever you want to update convo content:

1. **Download `convos.xlsx`** from the repo.
2. **Edit it locally** in Excel, Numbers, or Google Sheets (re-save as
   `.xlsx` if you use Sheets).
3. **Re-upload it** — repo root → "Add file" → "Upload files" → drag in
   the new `.xlsx` → commit.
4. **Wait ~30 seconds.** The Action runs automatically.
5. **Refresh your live site.** New content is there.

## What gets auto-generated vs. hand-edited

**Auto-generated from the spreadsheet** (don't hand-edit these —
they'll be overwritten):
- `index.html`
- 12 convo detail pages (e.g. `right-answers.html`)

**Hand-edited only** (edit directly in GitHub if you want to change
these):
- `about.html`
- `tips.html`
- `styles.css`
- Anything in `/pdfs/`

**Manual one-off** (the spreadsheet workflow doesn't help):
- Adding or replacing a PDF in `/pdfs/`. Same drag-and-drop flow as
  always.

## Adding a 13th convo

1. Add a row to `convos.xlsx` with Convo # = 13 and all the columns
   filled in.
2. Upload the spreadsheet to GitHub.
3. The Action will create `your-new-slug.html` automatically (slug
   derived from the Short Title — e.g. "My New Topic" →
   `my-new-topic.html`).
4. Manually upload the merged PDF to `pdfs/your-new-slug.pdf`. If it's a
   PDF spark, also upload `pdfs/sparks/your-new-slug-spark.pdf`.

## Decisions baked in (in case you want to change them)

- **Spreadsheet still uses the column names "Focus Lesson Name" and
  "Focus Lesson URL"**, but the UI labels them "reference lesson"
  everywhere. The column names were left alone for spreadsheet
  stability. To rename them, edit `generate_pages.py` (two lines).
- **Locked URLs for the first 11 convos.** Even if you rename a "Short
  Title," the URL stays stable so existing PDFs don't break. Edit
  `LOCKED_SLUGS` in `generate_pages.py` to change.
- **Theme order** (Deepening → Discourse → Real World) is hardcoded in
  `THEME_ORDER` near the top of `generate_pages.py`.
- **Theme-lesson callouts** (e.g. "Big Foot Conspiracy by Citizen Math")
  are in `THEME_LESSONS`. Add a new theme there or new lessons live
  there too.
- **The Action only commits when HTML actually changed**, so it won't
  clutter your commit history with empty re-runs.

## If something looks off

- **Action shows a red X (failed):** Click into it and read the error.
  Most likely a bad spreadsheet — missing column, unexpected value.
- **Site doesn't reflect changes after 1-2 minutes:** Hard-refresh the
  page (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows).
- **You want to force a re-run:** Actions tab → click the workflow →
  "Run workflow" button (top right) → click the green button.

## Running locally (optional)

To preview the site before pushing:

```bash
pip install pandas openpyxl
python3 generate_pages.py
python3 -m http.server 8000
# open http://localhost:8000
```

This regenerates the HTML and serves the folder on
`http://localhost:8000`.

---

Two extra files in this folder you can ignore unless something is
unexpected:

- **PLAN.md** — the reasoning for this overnight build, written before
  the work started. Useful if anything in the result is surprising.
- **CHANGES.md** — what got decided, what got verified, what to do if
  it doesn't behave. Read this if you want the full picture.
