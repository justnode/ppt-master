#!/usr/bin/env python3
"""PPT Master - SVG to HTML slideshow tool (thin wrapper).

Delegates to the svg_to_pptx package. The command name is kept for CLI
backward compatibility:
    uv run python3 scripts/svg_to_pptx.py <project_path> -s final
"""

import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so the package can be found
sys.path.insert(0, str(Path(__file__).resolve().parent))

from svg_to_pptx import main

if __name__ == '__main__':
    main()
