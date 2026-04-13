# SVG Pipeline Tools

These tools cover post-processing, SVG validation, speaker notes, and PPTX export.

Commands in this document assume your current working directory is the installed `ppt-master` skill root.

## Recommended Pipeline

Run these steps in order:

```bash
uv run python3 scripts/total_md_split.py <project_path>
uv run python3 scripts/finalize_svg.py <project_path>
uv run python3 scripts/svg_to_pptx.py <project_path> -s final
```

## `finalize_svg.py`

Unified post-processing entry point. This is the preferred way to run SVG cleanup.

It aggregates:
- `embed_icons.py`
- `crop_images.py`
- `fix_image_aspect.py`
- `embed_images.py`
- `flatten_tspan.py`
- `svg_rect_to_path.py`

## `svg_to_pptx.py`

Convert project SVGs into PPTX.

```bash
uv run python3 scripts/svg_to_pptx.py <project_path> -s final
uv run python3 scripts/svg_to_pptx.py <project_path> -s final --only native
uv run python3 scripts/svg_to_pptx.py <project_path> -s final --only legacy
uv run python3 scripts/svg_to_pptx.py <project_path> -s final --no-notes
uv run python3 scripts/svg_to_pptx.py <project_path> -t none
uv run python3 scripts/svg_to_pptx.py <project_path> -s final --auto-advance 3
```

Behavior:
- Default output: timestamped pair in `exports/` — `<project_name>_<timestamp>.pptx` (native editable) + `<project_name>_<timestamp>_svg.pptx` (SVG snapshot)
- Recommended source directory: `svg_final/`
- Speaker notes are embedded automatically unless `--no-notes` is used

Dependency:

```bash
pip install python-pptx
```

## `total_md_split.py`

Split `total.md` into per-slide note files.

```bash
uv run python3 scripts/total_md_split.py <project_path>
uv run python3 scripts/total_md_split.py <project_path> -o <output_directory>
uv run python3 scripts/total_md_split.py <project_path> -q
```

Requirements:
- Each section begins with `# `
- Heading text matches the SVG filename
- Sections are separated by `---`

## `svg_quality_checker.py`

Validate SVG technical compliance.

```bash
uv run python3 scripts/svg_quality_checker.py examples/project/svg_output/01_cover.svg
uv run python3 scripts/svg_quality_checker.py examples/project/svg_output
uv run python3 scripts/svg_quality_checker.py examples/project
uv run python3 scripts/svg_quality_checker.py examples/project --format ppt169
uv run python3 scripts/svg_quality_checker.py --all examples
uv run python3 scripts/svg_quality_checker.py examples/project --export
```

Checks include:
- `viewBox`
- banned elements
- width/height consistency
- line-break structure

## `svg_position_calculator.py`

Analyze or pre-calculate chart coordinates.

Common commands:

```bash
uv run python3 scripts/svg_position_calculator.py analyze <svg_file>
uv run python3 scripts/svg_position_calculator.py interactive
uv run python3 scripts/svg_position_calculator.py calc bar --data "East:185,South:142"
uv run python3 scripts/svg_position_calculator.py calc pie --data "A:35,B:25,C:20"
uv run python3 scripts/svg_position_calculator.py from-json config.json
```

Use this when chart geometry needs to be verified before or after AI generation.

## Advanced Standalone Tools

### `flatten_tspan.py`

```bash
uv run python3 scripts/svg_finalize/flatten_tspan.py examples/<project>/svg_output
uv run python3 scripts/svg_finalize/flatten_tspan.py path/to/input.svg path/to/output.svg
```

### `svg_rect_to_path.py`

```bash
uv run python3 scripts/svg_finalize/svg_rect_to_path.py <project_path>
uv run python3 scripts/svg_finalize/svg_rect_to_path.py <project_path> -s final
uv run python3 scripts/svg_finalize/svg_rect_to_path.py path/to/file.svg
```

Use when rounded corners must survive PowerPoint shape conversion.

### `fix_image_aspect.py`

```bash
uv run python3 scripts/svg_finalize/fix_image_aspect.py path/to/slide.svg
uv run python3 scripts/svg_finalize/fix_image_aspect.py 01_cover.svg 02_toc.svg
uv run python3 scripts/svg_finalize/fix_image_aspect.py --dry-run path/to/slide.svg
```

Use when embedded images stretch after PowerPoint shape conversion.

### `embed_icons.py`

```bash
uv run python3 scripts/svg_finalize/embed_icons.py output.svg
uv run python3 scripts/svg_finalize/embed_icons.py svg_output/*.svg
uv run python3 scripts/svg_finalize/embed_icons.py --dry-run svg_output/*.svg
```

Replaces `<use data-icon="chunk/name" .../>`, `<use data-icon="tabler-filled/name" .../>` and `<use data-icon="tabler-outline/name" .../>` placeholders with actual SVG path elements. Use for manual icon embedding checks outside `finalize_svg.py`.

## PPT Compatibility Rules

Use PowerPoint-safe transparency syntax:

| Avoid | Use instead |
|------|-------------|
| `fill=\"rgba(...)\"` | `fill=\"#hex\"` + `fill-opacity` |
| `<g opacity=\"...\">` | Set opacity on each child |
| `<image opacity=\"...\">` | Overlay with a mask layer |

PowerPoint also has trouble with:
- marker-based arrows
- unsupported filters
- direct SVG features not mapped to DrawingML
