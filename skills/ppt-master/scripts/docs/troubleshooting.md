# Troubleshooting

Commands in this document assume your current working directory is the installed `ppt-master` skill root unless stated otherwise.

## Validation Failed

1. Run:

```bash
uv run python3 scripts/project_manager.py validate <project_path>
```

2. Fix missing files or invalid directories reported by the validator.
3. Re-run validation before post-processing or export.

## SVG Preview Looks Wrong

1. Check the file path and filename.
2. Confirm naming conventions are consistent.
3. Preview via a local server if browser file loading is inconsistent:

```bash
uv run python3 -m http.server --directory <svg_output_path> 8000
```

## Speaker Notes Do Not Split

Check `total.md`:
- headings must start with `# `
- heading text must match SVG filenames
- sections must be separated by `---`

Then rerun:

```bash
uv run python3 scripts/total_md_split.py <project_path>
```

## PPT Export Quality Issues

Preferred sequence:

```bash
uv run python3 scripts/total_md_split.py <project_path>
uv run python3 scripts/finalize_svg.py <project_path>
uv run python3 scripts/svg_to_pptx.py <project_path> -s final
```

Do not export directly from `svg_output/` when `svg_final/` exists.

## Dependency Checklist

Most tools use the standard library. Install extra dependencies only when needed:

```bash
uv sync --project .
```

This command creates the primary environment at `.venv` under the installed skill root.

When you are running from a globally installed `~/.agents/skills/ppt-master` directory, the Python entry scripts will auto-bootstrap from its local `pyproject.toml` when `uv` is available.

Important optional packages:
- `python-pptx` for PPTX export
- `Pillow` for image utilities
- `numpy` for watermark removal
- `PyMuPDF` for PDF conversion
- `google-genai` / `openai` for image generation backends
