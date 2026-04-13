# Image Tools

Image tools cover prompt-based generation, image inspection, and Gemini watermark removal.

Commands in this document assume your current working directory is the installed `ppt-master` skill root.

## `image_gen.py`

Unified image generation entry point.

```bash
uv run python3 scripts/image_gen.py "A modern futuristic workspace"
uv run python3 scripts/image_gen.py "Abstract tech background" --aspect_ratio 16:9 --image_size 4K
uv run python3 scripts/image_gen.py "Concept car" -o projects/demo/images
uv run python3 scripts/image_gen.py "Beautiful landscape" -n "low quality, blurry, watermark"
uv run python3 scripts/image_gen.py --list-backends
```

Support tiers:
- Core: `gemini`, `openai`, `qwen`, `zhipu`, `volcengine`
- Extended: `stability`, `bfl`, `ideogram`
- Experimental: `minimax`, `siliconflow`, `fal`, `replicate`

Backend selection:

```bash
uv run python3 scripts/image_gen.py "A cat" --backend openai
uv run python3 scripts/image_gen.py "A cinematic portrait" --backend minimax
uv run python3 scripts/image_gen.py "A product launch hero image" --backend qwen
uv run python3 scripts/image_gen.py "科技感背景图" --backend zhipu
uv run python3 scripts/image_gen.py "A product KV in cinematic style" --backend volcengine
```

Configuration sources:

1. Current process environment variables
2. The nearest `.env` found by walking upward from the current working directory

The active backend must always be selected explicitly via `IMAGE_BACKEND`.

Example `.env`:

```env
IMAGE_BACKEND=gemini
GEMINI_API_KEY=your-api-key
GEMINI_BASE_URL=https://your-proxy-url.com/v1beta
GEMINI_MODEL=gemini-3.1-flash-image-preview
```

Example process environment:

```bash
export IMAGE_BACKEND=gemini
export GEMINI_API_KEY=your-api-key
export GEMINI_MODEL=gemini-3.1-flash-image-preview
```

Current process environment wins over `.env`.

Use provider-specific keys only, such as `GEMINI_API_KEY`, `OPENAI_API_KEY`, `MINIMAX_API_KEY`, `QWEN_API_KEY`, `ZHIPU_API_KEY`, `VOLCENGINE_API_KEY`, `FAL_KEY`, or `REPLICATE_API_TOKEN`.

`IMAGE_API_KEY`, `IMAGE_MODEL`, and `IMAGE_BASE_URL` are intentionally unsupported.

If you keep multiple providers in one `.env` or environment, `IMAGE_BACKEND` must explicitly select the active provider.

Recommendation:
- Default to the Core tier for routine PPT work
- Use Extended only when you need a specific model style
- Treat Experimental backends as opt-in

## `analyze_images.py`

Analyze images in a project directory before writing the design spec or composing slide layouts.

```bash
uv run python3 scripts/analyze_images.py <project_path>/images
```

Use this instead of opening image files directly when following the project workflow.

## `gemini_watermark_remover.py`

Remove Gemini watermark assets after manual download.

```bash
uv run python3 scripts/gemini_watermark_remover.py <image_path>
uv run python3 scripts/gemini_watermark_remover.py <image_path> -o output_path.png
uv run python3 scripts/gemini_watermark_remover.py <image_path> -q
```

Notes:
- Requires `scripts/assets/bg_48.png` and `scripts/assets/bg_96.png`
- Best used after downloading “full size” Gemini images

Dependencies:

```bash
pip install Pillow numpy
```
