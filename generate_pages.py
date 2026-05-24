#!/usr/bin/env python3
"""
Convos with Colleagues — page generator (Version C styling).

Reads `convos.xlsx` (sheet "Convos", header on row 2) and regenerates every
convo detail page (e.g. right-answers.html) plus index.html.

Run locally:
    pip install pandas openpyxl
    python generate_pages.py

The GitHub Action (.github/workflows/build.yml) runs this automatically
whenever `convos.xlsx` is updated in the repo.

What this script DOES touch:
    - One HTML file per convo, named from a slug derived from "Short Title"
    - index.html (the homepage)

What this script DOES NOT touch:
    - about.html, tips.html (hand-edited)
    - styles.css
    - PDFs in /pdfs/

If you rename a "Short Title" in the spreadsheet, the slug changes and a
new HTML file is created. The old one stays behind until you delete it
from the repo manually.

Spreadsheet column reference:
    Convo #, Short Title, Title / Question, Overview / Description, Theme,
    Focus Lesson Name, Focus Lesson URL, Spark Type, Spark Label,
    Spark Caption, Spark URL,
    Observe Q1-Q2, Discuss Q1-Q3, Relate Q1-Q3, Commit Q1.

The "Focus Lesson" column names are preserved for spreadsheet stability, but
the rendered UI labels them as "reference lesson" everywhere.
"""

import os
import re
import sys
from urllib.parse import quote

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas openpyxl")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SPREADSHEET_PATH = os.environ.get("CWC_SPREADSHEET", "convos.xlsx")
SHEET_NAME = "Convos"
HEADER_ROW = 1  # 0-indexed; the actual header is on spreadsheet row 2
OUTPUT_DIR = os.environ.get("CWC_OUTPUT_DIR", ".")

# Order of themes on the homepage. Any theme found in the spreadsheet but
# not listed here is appended to the bottom in alphabetical order.
THEME_ORDER = [
    "Deepening Mathematical Understanding",
    "Fostering Student Discourse",
    "Focusing on the Real World",
]

# Locked slugs for existing convos, so URLs and PDF filenames stay stable
# even if you tweak the "Short Title" in the spreadsheet. Keyed by Convo #.
# If you add a 12th convo (or beyond), it auto-slugs from its Short Title.
# To rename an existing convo's URL: update the slug here AND rename its
# PDFs in /pdfs/ to match.
LOCKED_SLUGS = {
    1:  "sequencing-student-work",
    2:  "right-answers",
    3:  "wrong-answers",
    4:  "get-started",
    5:  "physical-classroom",
    6:  "student-to-student",
    7:  "complex-problems",
    8:  "voices-and-perspectives",
    9:  "rabbit-holes",
    10: "sensitive-topics",
    11: "open-ended-questions",
}

# Map theme → list of (lesson name, lesson URL) tuples used as the Spark
# anchor for that theme. Update if you add new themes.
THEME_LESSONS = {
    "Deepening Mathematical Understanding": [
        ("Hair Today, Gone Tomorrow",
         "https://www.citizenmath.com/lessons/_template.html?slug=hair-today-gone-tomorrow"),
    ],
    "Fostering Student Discourse": [
        ("Big Foot Conspiracy",
         "https://www.citizenmath.com/lessons/_template.html?slug=big-foot-conspiracy"),
    ],
    "Focusing on the Real World": [
        ("Big Foot Conspiracy",
         "https://www.citizenmath.com/lessons/_template.html?slug=big-foot-conspiracy"),
        ("Seeking Shelter",
         "https://www.citizenmath.com/lessons/_template.html?slug=seeking-shelter"),
        ("Coupon Clipping",
         "https://www.citizenmath.com/lessons/_template.html?slug=coupon-clipping"),
    ],
}


# ---------------------------------------------------------------------------
# Reusable building blocks — shared across all generated pages
# ---------------------------------------------------------------------------

GOOGLE_FONTS_LINK = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Corben:wght@400;700&'
    'family=Caveat:wght@500;600;700&'
    'family=Inter:wght@400;500;600&'
    'display=swap" rel="stylesheet">'
)


SITE_HEADER = '''  <header class="site-header">
    <div class="site-header-inner">
      <a href="index.html" class="site-logo" aria-label="Convos with Colleagues home">
        <img src="logo-darkbg.svg" alt="Convos with Colleagues" class="site-logo-img">
      </a>
      <nav class="site-nav">
        <a href="about.html">About the Convos</a>
        <a href="tips.html">Tips for a Great Convo</a>
      </nav>
    </div>
  </header>'''


# Variant used on the homepage only — no logo (since the giant hero logo
# sits immediately below, repeating it in the header is redundant).
INDEX_HEADER = '''  <header class="site-header site-header-index">
    <div class="site-header-inner">
      <span class="site-header-spacer" aria-hidden="true"></span>
      <nav class="site-nav">
        <a href="about.html">About the Convos</a>
        <a href="tips.html">Tips for a Great Convo</a>
      </nav>
    </div>
  </header>'''


SITE_FOOTER = '''  <footer class="site-footer">
    <p class="footer-tagline">A professional learning resource. Use freely.</p>
  </footer>'''


SPARK_ICON_SVG = (
    '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" '
    'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true">'
    '<polyline points="7 3 4 13 11 13 8 21 20 9 13 9 16 3 7 3"/></svg>'
)


EYE_ICON_SVG = (
    '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" '
    'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
    'stroke-linejoin="round">'
    '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/>'
    '<circle cx="12" cy="12" r="3"/></svg>'
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text):
    """Convert a string into a URL-friendly slug.
    'Right Answers' -> 'right-answers'
    'Open-Ended Questions' -> 'open-ended-questions'
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[''""]", "", text)  # drop fancy quotes
    text = re.sub(r"[^a-z0-9]+", "-", text)  # non-alphanumeric -> hyphen
    text = re.sub(r"^-+|-+$", "", text)  # trim hyphens
    return text


def extract_vimeo_id(url):
    """Pull a Vimeo ID out of a URL like https://vimeo.com/12345.
    Returns None for anything that doesn't match."""
    if not url:
        return None
    m = re.search(r"vimeo\.com/(\d+)", str(url))
    return m.group(1) if m else None


def safe(val):
    """Coerce pandas value to a clean string, or '' if NaN/empty."""
    if val is None:
        return ""
    if isinstance(val, float):
        import math
        if math.isnan(val):
            return ""
    return str(val).strip()


def render_share_url(title):
    """Build a mailto: URL for the 'Invite colleagues' button."""
    subject = "Let's have a Conversation with a Colleague"
    body = (
        f"I came across this discussion guide and thought we could work through it together.\n\n"
        f"{title}\n\n"
        f"[paste page URL here]\n\n"
        f"It's designed for 2–5 people, 30–60 minutes. Want to pick a time?"
    )
    return f"mailto:?subject={quote(subject)}&body={quote(body)}"


# ---------------------------------------------------------------------------
# Spreadsheet loading
# ---------------------------------------------------------------------------

def load_convos():
    """Read the spreadsheet and return a list of cleaned convo dicts."""
    if not os.path.exists(SPREADSHEET_PATH):
        print(f"ERROR: Spreadsheet not found at {SPREADSHEET_PATH}")
        sys.exit(1)

    df = pd.read_excel(SPREADSHEET_PATH, sheet_name=SHEET_NAME, header=HEADER_ROW)

    # Filter to rows with a numeric Convo #
    df = df[pd.to_numeric(df["Convo #"], errors="coerce").notna()]

    # Spark Type column has a newline in the header. Map to a clean key.
    spark_type_col = next(
        (c for c in df.columns if c.lower().startswith("spark type")), None
    )
    if not spark_type_col:
        print("ERROR: Couldn't find 'Spark Type' column in spreadsheet.")
        sys.exit(1)

    convos = []
    for _, row in df.iterrows():
        num = int(row["Convo #"])
        short = safe(row["Short Title"])
        # Use locked slug if this is one of the original convos; otherwise derive
        slug = LOCKED_SLUGS.get(num) or slugify(short)
        if not slug:
            print(f"ERROR: Convo #{num} has no Short Title and is not in LOCKED_SLUGS.")
            sys.exit(1)
        convos.append({
            "num": num,
            "slug": slug,
            "short_title": short,
            "title": safe(row["Title / Question"]),
            "overview": safe(row["Overview / Description"]),
            "theme": safe(row["Theme"]),
            # The spreadsheet column is still named "Focus Lesson" but we
            # render it as "reference lesson" in the UI.
            "ref_lesson_name": safe(row["Focus Lesson Name"]),
            "ref_lesson_url": safe(row["Focus Lesson URL"]),
            "spark_type": safe(row[spark_type_col]),
            "spark_label": safe(row["Spark Label"]),
            "spark_caption": safe(row["Spark Caption"]),
            "spark_url": safe(row["Spark URL"]),
            "observe_q1": safe(row.get("Observe Q1")),
            "observe_q2": safe(row.get("Observe Q2")),
            "discuss_q1": safe(row.get("Discuss Q1")),
            "discuss_q2": safe(row.get("Discuss Q2")),
            "discuss_q3": safe(row.get("Discuss Q3")),
            "relate_q1": safe(row.get("Relate Q1")),
            "relate_q2": safe(row.get("Relate Q2")),
            "relate_q3": safe(row.get("Relate Q3")),
            "commit_q1": safe(row.get("Commit Q1")),
        })

    # Sanity-check slugs are unique
    slugs = [c["slug"] for c in convos]
    if len(slugs) != len(set(slugs)):
        from collections import Counter
        dupes = [s for s, n in Counter(slugs).items() if n > 1]
        print(f"ERROR: Duplicate slugs from Short Titles: {dupes}")
        sys.exit(1)

    return sorted(convos, key=lambda c: c["num"])


# ---------------------------------------------------------------------------
# Detail page rendering
# ---------------------------------------------------------------------------

# Phase metadata — number, label, time. Drives the section headers.
PHASES = [
    ("observe", 1, "Observe", "5–15 min"),
    ("discuss", 2, "Discuss", "10–15 min"),
    ("relate",  3, "Relate",  "10–15 min"),
    ("commit",  4, "Commit",  "5–10 min"),
]


def render_questions_ul(*qs):
    """Build the inner <li> items of a questions list, skipping blanks."""
    items = [q for q in qs if q]
    if not items:
        return ""
    return "\n          ".join(f"<li>{q}</li>" for q in items)


def render_section(section_id, num, h2, time_label, body_inner):
    """One phase section, with the colored numbered circle in the header."""
    return f'''
      <section class="section" id="{section_id}">
        <button class="section-header" type="button" aria-expanded="true" aria-controls="{section_id}-body">
          <span class="section-num" aria-hidden="true">{num}</span>
          <h2>{h2}</h2>
          <span class="section-time">{time_label}</span>
          <span class="section-toggle" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
          </span>
        </button>
        <div class="section-body" id="{section_id}-body">
{body_inner}
        </div>
      </section>'''


def render_video_spark(vimeo_id, label, caption):
    """Spark inset for a Vimeo-hosted animated video."""
    return f'''<aside class="spark-inset spark-inset-video" role="complementary">
            <div class="spark-inset-thumb">
              <img src="https://vumbnail.com/{vimeo_id}.jpg" alt="" onerror="this.style.display='none'">
              <button class="spark-play-button" type="button" data-video-id="{vimeo_id}" aria-label="Play animated video">
                <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>
              </button>
            </div>
            <div class="spark-inset-body">
              <span class="spark-inset-label">Spark Artifact · {label}</span>
              <p class="spark-inset-caption">{caption}</p>
              <button class="spark-inset-cta" type="button" data-video-id="{vimeo_id}">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><polygon points="6 4 20 12 6 20 6 4"/></svg>
                Watch the video
              </button>
            </div>
          </aside>'''


def render_pdf_spark(slug, label, caption):
    """Spark inset for a downloadable PDF (fanned-page thumbnail)."""
    pdf_href = f"pdfs/sparks/{slug}-spark.pdf"
    return f'''<aside class="spark-inset spark-inset-pdf" role="complementary">
            <a class="spark-inset-thumb spark-inset-thumb-pdf" href="{pdf_href}" target="_blank" rel="noopener" aria-label="Open the spark PDF in a new tab">
              <span class="fanned-page fanned-page-back" aria-hidden="true">
                <span class="fanned-lines"><span></span><span></span><span></span><span></span><span></span></span>
              </span>
              <span class="fanned-page fanned-page-front" aria-hidden="true">
                <span class="fanned-lines"><span></span><span></span><span></span><span></span><span></span><span></span></span>
              </span>
            </a>
            <div class="spark-inset-body">
              <span class="spark-inset-label">Spark Artifact · {label}</span>
              <p class="spark-inset-caption">{caption}</p>
              <a class="spark-inset-cta" href="{pdf_href}" target="_blank" rel="noopener">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3v4a1 1 0 0 0 1 1h4"/><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z"/></svg>
                Open the PDF
              </a>
            </div>
          </aside>'''


def render_video_modal():
    """Modal markup, only included when a page has a video spark."""
    return '''
  <div class="video-modal" id="video-modal" role="dialog" aria-modal="true" aria-label="Video player" hidden>
    <div class="video-modal-backdrop" data-close-modal></div>
    <div class="video-modal-content">
      <button class="video-modal-close" type="button" data-close-modal aria-label="Close video">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
      <div class="video-modal-frame">
        <iframe id="video-modal-iframe" src="" allow="autoplay; fullscreen; picture-in-picture; clipboard-write; encrypted-media; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
      </div>
    </div>
  </div>'''


def render_detail_scripts(has_video):
    """Combined script block — section-collapse always, video-modal if needed."""
    video_block = ""
    if has_video:
        video_block = '''
      var modal = document.getElementById('video-modal');
      var iframe = document.getElementById('video-modal-iframe');
      function openVideo(id) {
        iframe.src = 'https://player.vimeo.com/video/' + id + '?autoplay=1&title=0&byline=0&portrait=0&badge=0&autopause=0&player_id=0&app_id=58479';
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
      }
      function closeVideo() {
        iframe.src = '';
        modal.hidden = true;
        document.body.style.overflow = '';
      }
      document.querySelectorAll('[data-video-id]').forEach(function(el) {
        el.addEventListener('click', function() { openVideo(el.getAttribute('data-video-id')); });
      });
      document.querySelectorAll('[data-close-modal]').forEach(function(el) {
        el.addEventListener('click', closeVideo);
      });
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.hidden) closeVideo();
      });'''
    return f'''
  <script>
    (function() {{{video_block}
      document.querySelectorAll('.section-header').forEach(function(header) {{
        header.addEventListener('click', function() {{
          var section = header.parentElement;
          var expanded = header.getAttribute('aria-expanded') === 'true';
          header.setAttribute('aria-expanded', String(!expanded));
          section.classList.toggle('section-collapsed', expanded);
        }});
      }});
    }})();
  </script>'''


def render_detail_page(convo):
    """Render a single convo detail page in Version C styling."""
    vimeo_id = extract_vimeo_id(convo["spark_url"])
    is_video = vimeo_id is not None
    slug = convo["slug"]

    if is_video:
        spark_html = render_video_spark(
            vimeo_id, convo["spark_label"], convo["spark_caption"]
        )
    else:
        spark_html = render_pdf_spark(
            slug, convo["spark_label"], convo["spark_caption"]
        )

    # Build the four phase bodies. Only observe has the spark inset.
    observe_body = f'''          {spark_html}
          <ul class="questions">
          {render_questions_ul(convo['observe_q1'], convo['observe_q2'])}
          </ul>'''

    discuss_body = f'''          <ul class="questions">
          {render_questions_ul(convo['discuss_q1'], convo['discuss_q2'], convo['discuss_q3'])}
          </ul>'''

    relate_body = f'''          <ul class="questions">
          {render_questions_ul(convo['relate_q1'], convo['relate_q2'], convo['relate_q3'])}
          </ul>'''

    commit_body = f'''          <ul class="questions">
          {render_questions_ul(convo['commit_q1'])}
          </ul>'''

    phase_bodies = {
        "observe": observe_body,
        "discuss": discuss_body,
        "relate":  relate_body,
        "commit":  commit_body,
    }

    sections = "".join(
        render_section(pid, num, h2, time_label, phase_bodies[pid])
        for (pid, num, h2, time_label) in PHASES
    )

    download_url = f"pdfs/{slug}.pdf"

    # Build the right-column prep-zone (action buttons).
    # The "Preview the reference lesson" button only appears if a URL exists.
    reference_lesson_button = ""
    if convo["ref_lesson_url"]:
        reference_lesson_button = f'''
            <a class="prep-action-btn" href="{convo['ref_lesson_url']}" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>
              Preview the reference lesson
            </a>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{convo['title']} · Convos with Colleagues</title>
  <meta name="description" content="A roundtable discussion guide for math teachers.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  {GOOGLE_FONTS_LINK}
  <link rel="stylesheet" href="styles.css">
</head>
<body>

{SITE_HEADER}

  <main>

    <div class="hero-meta">
      <span><span class="num">30–60</span>min</span>
      <span><span class="num">2–5</span>educators</span>
      <span>no facilitator needed</span>
    </div>

    <section class="detail-hero">
      <div class="detail-hero-inner">
        <div class="detail-hero-content">
          <div class="hero-theme">{convo['theme']}</div>
          <h1>{convo['title']}</h1>
          <p class="overview">{convo['overview']}</p>
        </div>
        <section class="prep-zone" aria-labelledby="get-ready">
          <div class="prep-actions">
            <a class="prep-action-btn" href="{render_share_url(convo['title'])}">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              Invite colleagues
            </a>
            <a class="prep-action-btn" href="{download_url}" download>
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Print Convo Guide
            </a>{reference_lesson_button}
          </div>
        </section>
      </div>
    </section>

    <div class="container">
{sections}

    </div>

  </main>

{SITE_FOOTER}
{render_video_modal() if is_video else ''}
{render_detail_scripts(is_video)}

</body>
</html>
'''


# ---------------------------------------------------------------------------
# Index (homepage) rendering
# ---------------------------------------------------------------------------

def render_theme_lesson_block(theme):
    """The 'Real-World Math lesson used for Spark: <em>X</em> by Citizen Math'
    line under each theme header."""
    lessons = THEME_LESSONS.get(theme, [])
    if not lessons:
        return ""

    label = ("Real-World Math lesson used for Spark:" if len(lessons) == 1
             else "Real-World Math lessons used for Spark:")

    link_pieces = []
    for i, (name, url) in enumerate(lessons):
        link = (f'<a class="theme-lesson-link" href="{url}" '
                f'target="_blank" rel="noopener"><em>{name}</em></a>')
        if i < len(lessons) - 1:
            sep_text = "," if i < len(lessons) - 2 else ", &amp;"
            link_pieces.append(f'{link}<span class="theme-lesson-sep">{sep_text}</span>')
        else:
            link_pieces.append(link)

    links_html = "\n            ".join(link_pieces)

    return f'''<div class="theme-lesson">
            <span class="theme-lesson-icon" aria-hidden="true">
              {EYE_ICON_SVG}
            </span>
            <span class="theme-lesson-label">{label}</span>
            {links_html}
            <span class="theme-lesson-credit">by Citizen Math</span>
          </div>'''


def render_card(convo):
    """One <a class="convo-card"> inside the carousel shelf."""
    return f'''
            <a class="convo-card" href="{convo['slug']}.html">
              <span class="convo-short">{convo['short_title']}</span>
              <span class="convo-question">{convo['title']}</span>
              <span class="convo-spark">
                {SPARK_ICON_SVG}
                {convo['spark_label']}
              </span>
            </a>'''


def render_theme_section(theme, convos_in_theme):
    """A whole theme section: header + lesson callout + carousel shelf."""
    lesson_block = render_theme_lesson_block(theme)
    cards_html = "".join(render_card(c) for c in convos_in_theme)

    return f'''
      <section class="theme-section">
        <header class="theme-header">
          <h2>{theme}</h2>
          {lesson_block}
        </header>
        <div class="convo-shelf">
          <div class="convo-shelf-fade convo-shelf-fade-left"></div>
          <div class="convo-shelf-fade convo-shelf-fade-right"></div>
          <button class="convo-shelf-arrow convo-shelf-arrow-left" type="button" aria-label="Scroll left">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <button class="convo-shelf-arrow convo-shelf-arrow-right" type="button" aria-label="Scroll right">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          </button>
          <div class="convo-shelf-track">{cards_html}
          </div>
        </div>
      </section>'''


INDEX_BANNERS = '''
    <!-- DARK SLATE BANNER: What's in each convo -->
    <section class="banner-whats">
      <div class="banner-whats-inner">
        <div class="banner-header">
          <span class="banner-eyebrow">Anatomy of a convo</span>
          <h2>What's in each convo</h2>
        </div>
        <div class="banner-3up">
          <div class="banner-item">
            <svg class="banner-item-icon" viewBox="0 0 100 100" fill="none" aria-hidden="true">
              <path d="M15 28 C 16 18, 22 14, 32 14 L 70 13 C 82 12, 88 18, 88 30 L 87 56 C 88 66, 82 72, 70 73 L 48 73 L 32 88 L 34 73 L 30 73 C 20 72, 14 67, 14 56 Z"
                    stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M28 36 L 72 36" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M28 47 L 62 47" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M28 58 L 56 58" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
            <h3>Convo Guide</h3>
            <p>Carefully crafted questions to guide a productive discussion without a facilitator.</p>
          </div>
          <div class="banner-item">
            <svg class="banner-item-icon" viewBox="0 0 100 100" fill="none" aria-hidden="true">
              <path d="M55 8 L 22 56 L 44 56 L 36 92 L 78 38 L 54 38 L 62 8 Z"
                    stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="M14 24 L 22 28 M 18 18 L 18 28" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M82 62 L 90 66 M 86 56 L 86 70" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              <circle cx="84" cy="20" r="2.5" fill="currentColor"/>
              <circle cx="16" cy="78" r="2.5" fill="currentColor"/>
            </svg>
            <h3>Spark</h3>
            <p>A short video, classroom transcript, or piece of student work to ground the discussion.</p>
          </div>
          <div class="banner-item">
            <svg class="banner-item-icon" viewBox="0 0 100 100" fill="none" aria-hidden="true">
              <path d="M12 24 Q 30 18, 50 28 Q 70 18, 88 24 L 88 78 Q 70 72, 50 82 Q 30 72, 12 78 Z"
                    stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
              <path d="M50 28 L 50 82" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
              <path d="M22 38 L 42 41" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M22 48 L 42 51" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M22 58 L 38 60" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M58 41 L 78 38" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M58 51 L 78 48" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M58 60 L 74 58" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <h3>Reference Lesson</h3>
            <p>Each spark is contextualized in a high-quality lesson that's mathematically rigorous and rooted in the real world.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- DOODLE BRIDGE: pink hand-drawn arrow from dark banner's "Reference Lesson"
         column down to the peach banner that talks about reference lessons -->
    <div class="doodle-bridge" aria-hidden="true">
      <svg class="doodle-arrow" viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet">
        <!-- Squiggle path: starts near top-right (under "Reference Lesson"),
             curves down and leftward, ending with an arrowhead pointing
             at the peach banner heading. -->
        <path class="doodle-path"
              d="M 320 10 C 330 40, 290 50, 280 70 S 240 100, 230 125 S 200 160, 175 165"
              fill="none" stroke="#FF7978" stroke-width="3"
              stroke-linecap="round" stroke-linejoin="round" />
        <!-- Arrowhead: two small lines meeting at the end of the path -->
        <path class="doodle-head"
              d="M 165 155 L 175 165 L 187 158"
              fill="none" stroke="#FF7978" stroke-width="3"
              stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>

    <!-- HONEY AMBER BANNER: Can I get the reference lessons -->
    <section class="banner-lessons">
      <div class="banner-lessons-inner">
        <div>
          <h2>Can I get the reference lessons for myself?</h2>
          <p>Yes. Every Spark is contextualized in a Citizen Math lesson — mathematically rigorous, conversational, and rooted in the real world. You don't need to teach the lesson to use the convo, but having it on hand gives every participant a shared anchor for the discussion.</p>
          <a class="banner-cta" href="https://www.citizenmath.com" target="_blank" rel="noopener">
            Get the lessons at Citizen Math
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
          </a>
        </div>
        <div></div>
      </div>
    </section>'''


INDEX_CAROUSEL_SCRIPT = '''
  <script>
    // Adaptive carousel: only show arrows/fades when content overflows
    (function() {
      document.querySelectorAll('.convo-shelf').forEach(function(shelf) {
        var track = shelf.querySelector('.convo-shelf-track');
        var arrowL = shelf.querySelector('.convo-shelf-arrow-left');
        var arrowR = shelf.querySelector('.convo-shelf-arrow-right');

        function checkState() {
          var isOverflowing = track.scrollWidth > track.clientWidth + 2;
          shelf.classList.toggle('is-overflowing', isOverflowing);
          shelf.classList.toggle('at-start', track.scrollLeft <= 4);
          shelf.classList.toggle('at-end', track.scrollLeft + track.clientWidth >= track.scrollWidth - 4);
        }

        function scrollByOne(dir) {
          var card = track.querySelector('.convo-card');
          if (!card) return;
          var step = card.getBoundingClientRect().width + 20; // 1.25rem gap
          track.scrollBy({ left: dir * step, behavior: 'smooth' });
        }

        if (arrowL) arrowL.addEventListener('click', function() { scrollByOne(-1); });
        if (arrowR) arrowR.addEventListener('click', function() { scrollByOne(1); });
        track.addEventListener('scroll', checkState, { passive: true });
        window.addEventListener('resize', checkState);
        checkState();
      });
    })();

    // Doodle arrow: trigger the stroke-draw animation when scrolled into view
    (function() {
      var bridge = document.querySelector('.doodle-bridge');
      if (!bridge) return;
      if (!('IntersectionObserver' in window)) {
        bridge.classList.add('in-view');
        return;
      }
      var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            bridge.classList.add('in-view');
            observer.disconnect();
          }
        });
      }, { threshold: 0.3 });
      observer.observe(bridge);
    })();
  </script>'''


def render_index(convos):
    """Render the homepage from a list of convos."""
    # Group by theme, preserving spreadsheet order within each theme
    by_theme = {}
    for c in convos:
        by_theme.setdefault(c["theme"], []).append(c)

    # Order: themes in THEME_ORDER first, then any extras alphabetically
    ordered_themes = [t for t in THEME_ORDER if t in by_theme]
    extras = sorted(t for t in by_theme if t not in THEME_ORDER)
    ordered_themes.extend(extras)

    theme_sections_html = "".join(
        render_theme_section(theme, by_theme[theme]) for theme in ordered_themes
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Convos with Colleagues</title>
  <meta name="description" content="Roundtable discussions for math teachers serious about their craft.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  {GOOGLE_FONTS_LINK}
  <link rel="stylesheet" href="styles.css">
</head>
<body>

{INDEX_HEADER}

  <main>
    <section class="home-hero">
      <div class="home-hero-inner">
        <img src="logo-lightbg.svg" alt="Convos with Colleagues" class="home-hero-logo">

        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hero-stat-lead">Roundtable discussions</span>
            <span class="hero-stat-elab">around common instructional challenges in math class</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-lead">30–60 minutes</span>
            <span class="hero-stat-elab">low to no prep</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-lead">2–5 math teachers</span>
            <span class="hero-stat-elab">no facilitator needed</span>
          </div>
          <div class="hero-stat">
            <span class="hero-stat-lead">11 topics</span>
            <span class="hero-stat-elab">start anywhere you like</span>
          </div>
        </div>
      </div>
    </section>

    <div class="container-wide">
{theme_sections_html}
    </div>
{INDEX_BANNERS}
  </main>

{SITE_FOOTER}
{INDEX_CAROUSEL_SCRIPT}

</body>
</html>
'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    convos = load_convos()
    print(f"Loaded {len(convos)} convos from {SPREADSHEET_PATH}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Generate each detail page
    for convo in convos:
        path = os.path.join(OUTPUT_DIR, f"{convo['slug']}.html")
        with open(path, "w") as f:
            f.write(render_detail_page(convo))
        print(f"  ✓ {convo['slug']}.html ({convo['spark_type'] or 'no spark type'})")

    # Generate index
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w") as f:
        f.write(render_index(convos))
    print(f"  ✓ index.html ({len(convos)} convos across "
          f"{len({c['theme'] for c in convos})} themes)")

    print(f"\nDone. {len(convos) + 1} files written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
