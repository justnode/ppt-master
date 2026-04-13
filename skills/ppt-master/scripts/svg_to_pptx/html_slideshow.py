"""Single-file HTML slideshow export for project SVG pages."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from .pptx_dimensions import get_project_info
from .pptx_discovery import find_notes_files, find_svg_files


def _humanize_stem(stem: str) -> str:
    label = stem.replace("_", " ").replace("-", " ").strip()
    label = re.sub(r"\s+", " ", label)
    label = re.sub(r"^(?:slide|page|p)\s*\d+\s*", "", label, flags=re.IGNORECASE)
    label = re.sub(r"^\d+\s*", "", label)
    return label or "Untitled Slide"


def _html_id_for_slide(index: int) -> str:
    return f"slide-template-{index + 1:02d}"


def _build_html_document(
    *,
    project_title: str,
    slides: list[dict[str, str]],
    accent: str,
    auto_advance: float | None,
) -> str:
    slides_json = json.dumps(
        [
            {
                "templateId": slide["template_id"],
                "label": slide["label"],
                "note": slide["note"],
            }
            for slide in slides
        ],
        ensure_ascii=False,
    )
    auto_advance_ms = "null" if auto_advance is None else str(int(auto_advance * 1000))

    template_blocks = "\n".join(
        f'<template id="{slide["template_id"]}">\n{slide["svg"]}\n</template>'
        for slide in slides
    )

    safe_title = html.escape(project_title)
    safe_accent = html.escape(accent)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  :root {{
    --accent: {safe_accent};
    --bg: #070b14;
    --panel: rgba(255, 255, 255, 0.06);
    --panel-strong: rgba(255, 255, 255, 0.12);
    --border: rgba(255, 255, 255, 0.09);
    --text: rgba(255, 255, 255, 0.96);
    --muted: rgba(255, 255, 255, 0.58);
  }}

  body {{
    background:
      radial-gradient(circle at top left, rgba(99, 102, 241, 0.16), transparent 28%),
      radial-gradient(circle at top right, rgba(34, 211, 238, 0.14), transparent 24%),
      linear-gradient(180deg, #08101f 0%, #04070d 100%);
    color: var(--text);
    font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    overflow-x: hidden;
  }}

  .header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
    background: rgba(7, 11, 20, 0.8);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-bottom: 1px solid var(--border);
    padding: 14px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }}

  .header-left {{
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
  }}

  .header-logo {{
    width: 34px;
    height: 34px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--accent), #22d3ee);
    display: grid;
    place-items: center;
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    box-shadow: 0 10px 24px rgba(99, 102, 241, 0.28);
    flex-shrink: 0;
  }}

  .header-title {{
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .header-title span {{
    color: var(--accent);
    margin-right: 0.35em;
  }}

  .header-right {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }}

  .slide-counter {{
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--accent);
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }}

  .mode-btn {{
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 7px 14px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    transition: 0.2s ease;
  }}

  .mode-btn:hover {{
    background: var(--panel-strong);
  }}

  .mode-btn.active {{
    background: var(--accent);
    border-color: transparent;
    color: #fff;
  }}

  .gallery {{
    padding: 86px 28px 28px;
    max-width: 1440px;
    margin: 0 auto;
  }}

  .gallery-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 18px;
  }}

  .slide-card {{
    position: relative;
    background: rgba(9, 14, 24, 0.82);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
    padding: 14px;
    transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    cursor: pointer;
  }}

  .slide-card:hover {{
    transform: translateY(-4px);
    border-color: rgba(255, 255, 255, 0.18);
    box-shadow: 0 18px 38px rgba(0, 0, 0, 0.32);
  }}

  .slide-number {{
    position: absolute;
    top: 24px;
    left: 24px;
    z-index: 2;
    width: 30px;
    height: 30px;
    border-radius: 10px;
    background: rgba(0, 0, 0, 0.58);
    border: 1px solid rgba(255, 255, 255, 0.1);
    display: grid;
    place-items: center;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }}

  .slide-preview {{
    aspect-ratio: 16 / 9;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.04);
  }}

  .slide-label {{
    margin-top: 12px;
    color: rgba(255, 255, 255, 0.82);
    font-size: 13px;
    font-weight: 500;
    line-height: 1.45;
    min-height: 2.9em;
  }}

  .scroll-view {{
    display: none;
    padding: 86px 22px 40px;
  }}

  .scroll-view.active {{
    display: block;
  }}

  .scroll-slide {{
    max-width: 1040px;
    margin: 0 auto 20px;
    background: rgba(9, 14, 24, 0.78);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    padding: 12px;
    position: relative;
  }}

  .scroll-number {{
    position: absolute;
    top: 22px;
    left: 22px;
    z-index: 2;
    background: rgba(0, 0, 0, 0.55);
    color: #fff;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }}

  .scroll-preview {{
    width: 100%;
    aspect-ratio: 16 / 9;
    border-radius: 10px;
    overflow: hidden;
  }}

  .presentation {{
    display: none;
    position: fixed;
    inset: 0;
    z-index: 200;
    background: #000;
  }}

  .presentation.active {{
    display: flex;
    flex-direction: column;
  }}

  .pres-click-zone {{
    position: fixed;
    top: 0;
    bottom: 64px;
    width: 50%;
    z-index: 205;
  }}

  .pres-click-zone.left {{
    left: 0;
    cursor: w-resize;
  }}

  .pres-click-zone.right {{
    right: 0;
    cursor: e-resize;
  }}

  .pres-slide-container {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 22px;
  }}

  .pres-slide-host {{
    width: min(96vw, 1600px);
    height: calc(100vh - 92px);
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .pres-toolbar {{
    position: fixed;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    z-index: 210;
    background: rgba(0, 0, 0, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(18px);
    padding: 10px 16px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: min(88vw, 560px);
  }}

  .pres-btn {{
    width: 38px;
    height: 38px;
    border: none;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
    cursor: pointer;
    font-size: 17px;
    transition: background 0.2s ease;
  }}

  .pres-btn:hover {{
    background: rgba(255, 255, 255, 0.18);
  }}

  .pres-progress {{
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 999px;
    overflow: hidden;
  }}

  .pres-progress-bar {{
    height: 100%;
    width: 0;
    background: linear-gradient(90deg, var(--accent), #22d3ee);
    border-radius: 999px;
    transition: width 0.25s ease;
  }}

  .pres-counter {{
    min-width: 72px;
    text-align: center;
    color: rgba(255, 255, 255, 0.72);
    font-size: 13px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }}

  .notes-panel {{
    display: none;
    position: fixed;
    left: 22px;
    right: 22px;
    bottom: 82px;
    z-index: 215;
    max-width: 1080px;
    margin: 0 auto;
    background: rgba(7, 11, 20, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 18px;
    padding: 18px 22px;
    backdrop-filter: blur(20px);
    color: rgba(255, 255, 255, 0.86);
    max-height: 32vh;
    overflow-y: auto;
  }}

  .notes-panel.active {{
    display: block;
  }}

  .notes-title {{
    color: var(--accent);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}

  .notes-label {{
    font-size: 14px;
    line-height: 1.7;
    white-space: pre-wrap;
  }}

  .kbd-hint {{
    position: fixed;
    right: 18px;
    bottom: 18px;
    z-index: 60;
    background: rgba(8, 12, 20, 0.9);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 12px 14px;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.8;
  }}

  .kbd-hint kbd {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 5px;
    padding: 1px 6px;
    color: rgba(255, 255, 255, 0.82);
    font-size: 11px;
  }}

  @media (max-width: 900px) {{
    .header {{
      padding: 12px 16px;
      align-items: flex-start;
      flex-direction: column;
    }}

    .gallery {{
      padding: 120px 16px 18px;
    }}

    .gallery-grid {{
      grid-template-columns: 1fr;
    }}

    .scroll-view {{
      padding: 120px 10px 28px;
    }}

    .pres-slide-container {{
      padding: 10px;
    }}

    .pres-toolbar {{
      left: 12px;
      right: 12px;
      transform: none;
      min-width: 0;
    }}

    .kbd-hint {{
      display: none !important;
    }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="header-logo">PM</div>
    <div class="header-title"><span>HTML</span>{safe_title}</div>
  </div>
  <div class="header-right">
    <span class="slide-counter" id="slideCounter"></span>
    <button class="mode-btn active" data-mode="gallery" onclick="setMode('gallery')">Gallery</button>
    <button class="mode-btn" data-mode="scroll" onclick="setMode('scroll')">Scroll</button>
    <button class="mode-btn" data-mode="present" onclick="startPresentation(0)">Present</button>
  </div>
</div>

<div class="gallery" id="galleryView">
  <div class="gallery-grid" id="galleryGrid"></div>
</div>

<div class="scroll-view" id="scrollView"></div>

<div class="presentation" id="presView">
  <div class="pres-click-zone left" onclick="presNav(-1)"></div>
  <div class="pres-click-zone right" onclick="presNav(1)"></div>
  <div class="pres-slide-container">
    <div class="pres-slide-host" id="presSlide"></div>
  </div>
  <div class="notes-panel" id="notesPanel">
    <div class="notes-title">Speaker Notes</div>
    <div class="notes-label" id="notesContent"></div>
  </div>
  <div class="pres-toolbar">
    <button class="pres-btn" onclick="presNav(-1)">&#8592;</button>
    <div class="pres-progress"><div class="pres-progress-bar" id="presProgress"></div></div>
    <span class="pres-counter" id="presCounter"></span>
    <button class="pres-btn" onclick="presNav(1)">&#8594;</button>
    <button class="pres-btn" onclick="toggleNotes()">N</button>
    <button class="pres-btn" onclick="toggleFullscreen()">F</button>
    <button class="pres-btn" onclick="exitPresentation()">&#10005;</button>
  </div>
</div>

<div class="kbd-hint" id="kbdHint">
  <kbd>P</kbd> Present &nbsp;
  <kbd>G</kbd> Gallery &nbsp;
  <kbd>S</kbd> Scroll &nbsp;
  <kbd>N</kbd> Notes &nbsp;
  <kbd>F</kbd> Fullscreen &nbsp;
  <kbd>&larr;&rarr;</kbd> Navigate
</div>

{template_blocks}

<script>
const SLIDES = {slides_json};
const TOTAL = SLIDES.length;
const AUTO_ADVANCE_MS = {auto_advance_ms};

let currentMode = 'gallery';
let presIndex = 0;
let notesVisible = false;
let autoAdvanceTimer = null;

document.getElementById('slideCounter').textContent = `${{TOTAL}} slides`;

function renderSlideIntoHost(host, slide, mode) {{
  host.innerHTML = '';
  const mount = document.createElement('div');
  mount.style.width = '100%';
  mount.style.height = '100%';
  host.appendChild(mount);

  const shadow = mount.attachShadow({{ mode: 'open' }});
  const baseStyle = `
    :host {{
      display: block;
      width: 100%;
      height: 100%;
    }}
    * {{
      box-sizing: border-box;
    }}
    svg {{
      display: block;
      width: 100%;
      height: auto;
      margin: 0 auto;
    }}
  `;
  const presentStyle = `
    :host {{
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
    }}
    svg {{
      width: auto;
      max-width: 100%;
      max-height: 100%;
      height: auto;
      border-radius: 8px;
      box-shadow: 0 12px 42px rgba(0, 0, 0, 0.45);
      background: transparent;
    }}
  `;

  const template = document.getElementById(slide.templateId);
  shadow.innerHTML = `<style>${{mode === 'present' ? presentStyle : baseStyle}}</style>${{template.innerHTML}}`;
}}

function buildGallery() {{
  const galleryGrid = document.getElementById('galleryGrid');
  galleryGrid.innerHTML = '';
  SLIDES.forEach((slide, index) => {{
    const card = document.createElement('div');
    card.className = 'slide-card';
    card.onclick = () => startPresentation(index);

    const num = document.createElement('div');
    num.className = 'slide-number';
    num.textContent = String(index + 1).padStart(2, '0');

    const preview = document.createElement('div');
    preview.className = 'slide-preview';
    renderSlideIntoHost(preview, slide, 'gallery');

    const label = document.createElement('div');
    label.className = 'slide-label';
    label.textContent = slide.label;

    card.appendChild(num);
    card.appendChild(preview);
    card.appendChild(label);
    galleryGrid.appendChild(card);
  }});
}}

function buildScroll() {{
  const scrollView = document.getElementById('scrollView');
  scrollView.innerHTML = '';
  SLIDES.forEach((slide, index) => {{
    const wrap = document.createElement('div');
    wrap.className = 'scroll-slide';

    const num = document.createElement('div');
    num.className = 'scroll-number';
    num.textContent = `${{String(index + 1).padStart(2, '0')}} / ${{TOTAL}}`;

    const preview = document.createElement('div');
    preview.className = 'scroll-preview';
    renderSlideIntoHost(preview, slide, 'scroll');

    wrap.appendChild(num);
    wrap.appendChild(preview);
    scrollView.appendChild(wrap);
  }});
}}

function setMode(mode) {{
  currentMode = mode;
  document.getElementById('galleryView').style.display = mode === 'gallery' ? 'block' : 'none';
  document.getElementById('scrollView').classList.toggle('active', mode === 'scroll');
  document.getElementById('presView').classList.remove('active');
  document.getElementById('kbdHint').style.display = 'block';
  clearAutoAdvance();

  document.querySelectorAll('.mode-btn').forEach((button) => {{
    const targetMode = button.dataset.mode;
    button.classList.toggle('active', targetMode === mode);
  }});
}}

function startPresentation(index) {{
  presIndex = index || 0;
  currentMode = 'presentation';
  document.getElementById('presView').classList.add('active');
  document.getElementById('galleryView').style.display = 'none';
  document.getElementById('scrollView').classList.remove('active');
  document.getElementById('kbdHint').style.display = 'none';
  document.querySelectorAll('.mode-btn').forEach((button) => button.classList.remove('active'));
  renderPresentation();
  startAutoAdvance();
}}

function exitPresentation() {{
  document.getElementById('presView').classList.remove('active');
  document.getElementById('kbdHint').style.display = 'block';
  clearAutoAdvance();
  setMode('gallery');
}}

function presNav(delta) {{
  presIndex = Math.max(0, Math.min(TOTAL - 1, presIndex + delta));
  renderPresentation();
  startAutoAdvance();
}}

function updateNotes() {{
  const slide = SLIDES[presIndex];
  const note = slide.note && slide.note.trim() ? slide.note : `Slide ${{String(presIndex + 1).padStart(2, '0')}}: ${{slide.label}}`;
  document.getElementById('notesContent').textContent = note;
}}

function renderPresentation() {{
  const slide = SLIDES[presIndex];
  const host = document.getElementById('presSlide');
  renderSlideIntoHost(host, slide, 'present');
  document.getElementById('presCounter').textContent = `${{presIndex + 1}} / ${{TOTAL}}`;
  document.getElementById('presProgress').style.width = `${{((presIndex + 1) / TOTAL) * 100}}%`;
  updateNotes();
}}

function toggleNotes() {{
  notesVisible = !notesVisible;
  document.getElementById('notesPanel').classList.toggle('active', notesVisible);
}}

function toggleFullscreen() {{
  if (!document.fullscreenElement) {{
    document.documentElement.requestFullscreen?.();
  }} else {{
    document.exitFullscreen?.();
  }}
}}

function clearAutoAdvance() {{
  if (autoAdvanceTimer) {{
    window.clearTimeout(autoAdvanceTimer);
    autoAdvanceTimer = null;
  }}
}}

function startAutoAdvance() {{
  clearAutoAdvance();
  if (!AUTO_ADVANCE_MS || presIndex >= TOTAL - 1) {{
    return;
  }}
  autoAdvanceTimer = window.setTimeout(() => {{
    presNav(1);
  }}, AUTO_ADVANCE_MS);
}}

document.addEventListener('keydown', (event) => {{
  const inPresentation = document.getElementById('presView').classList.contains('active');
  if (inPresentation) {{
    if (event.key === 'ArrowRight' || event.key === ' ' || event.key === 'Enter') {{
      event.preventDefault();
      presNav(1);
    }} else if (event.key === 'ArrowLeft' || event.key === 'Backspace') {{
      event.preventDefault();
      presNav(-1);
    }} else if (event.key === 'Escape') {{
      exitPresentation();
    }} else if (event.key === 'Home') {{
      presIndex = 0;
      renderPresentation();
      startAutoAdvance();
    }} else if (event.key === 'End') {{
      presIndex = TOTAL - 1;
      renderPresentation();
      clearAutoAdvance();
    }} else if (event.key === 'n' || event.key === 'N') {{
      toggleNotes();
    }} else if (event.key === 'f' || event.key === 'F') {{
      toggleFullscreen();
    }}
    return;
  }}

  if (event.key === 'p' || event.key === 'P') {{
    startPresentation(0);
  }} else if (event.key === 'g' || event.key === 'G') {{
    setMode('gallery');
  }} else if (event.key === 's' || event.key === 'S') {{
    setMode('scroll');
  }} else if (event.key === 'f' || event.key === 'F') {{
    toggleFullscreen();
  }}
}});

buildGallery();
buildScroll();
setMode('gallery');
</script>
</body>
</html>
"""


def export_html_slideshow(
    *,
    project_path: Path,
    source: str,
    output: str | None,
    quiet: bool,
    include_notes: bool,
    auto_advance: float | None,
    title: str | None,
    accent: str,
) -> Path:
    svg_files, source_dir_name = find_svg_files(project_path, source)
    if not svg_files:
        raise SystemExit("Error: No SVG files found")

    project_info = get_project_info(str(project_path))
    project_name = project_info.get("name", project_path.name)
    project_title = title or str(project_name).replace("_", " ").strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output:
        output_path = Path(output)
    else:
        exports_dir = project_path / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        output_path = exports_dir / f"{project_path.name}_{timestamp}.html"

    notes = find_notes_files(project_path, svg_files) if include_notes else {}

    slides: list[dict[str, str]] = []
    for index, svg_path in enumerate(svg_files):
        slides.append(
            {
                "template_id": _html_id_for_slide(index),
                "label": _humanize_stem(svg_path.stem),
                "note": notes.get(svg_path.stem, ""),
                "svg": svg_path.read_text(encoding="utf-8"),
            }
        )

    document = _build_html_document(
        project_title=project_title,
        slides=slides,
        accent=accent,
        auto_advance=auto_advance,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")

    if not quiet:
        print("PPT Master - SVG to HTML Slideshow")
        print("=" * 50)
        print(f"  Project path: {project_path}")
        print(f"  SVG directory: {source_dir_name}")
        print(f"  Output file: {output_path}")
        print(f"  Slide count: {len(slides)}")
        print(f"  Notes: {'Enabled' if include_notes else 'Disabled'}")
        if auto_advance is not None:
            print(f"  Auto advance: {auto_advance:.1f}s")
        print()
        print(f"[Done] Saved: {output_path}")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PPT Master - SVG to HTML Slideshow Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s examples/ppt169_demo -s final
    %(prog)s examples/ppt169_demo -s final -o exports/demo.html
    %(prog)s examples/ppt169_demo -s final --auto-advance 4
    %(prog)s examples/ppt169_demo --no-notes
""",
    )
    parser.add_argument("project_path", type=str, help="Project directory path")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output HTML file path")
    parser.add_argument(
        "-s",
        "--source",
        type=str,
        default="output",
        help="SVG source: output/final or any subdirectory name (recommended: final)",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("--no-notes", action="store_true", help="Disable speaker notes panel content")
    parser.add_argument("--auto-advance", type=float, default=None, help="Auto-advance interval in seconds")
    parser.add_argument("--title", type=str, default=None, help="Override HTML page title")
    parser.add_argument("--accent", type=str, default="#6366f1", help="Accent color used by the viewer UI")

    args = parser.parse_args()
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Path does not exist: {project_path}")
        sys.exit(1)

    export_html_slideshow(
        project_path=project_path,
        source=args.source,
        output=args.output,
        quiet=args.quiet,
        include_notes=not args.no_notes,
        auto_advance=args.auto_advance,
        title=args.title,
        accent=args.accent,
    )


__all__ = ["export_html_slideshow", "main"]
