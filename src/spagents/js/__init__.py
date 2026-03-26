"""JavaScript file loader for spagents.

Loads .js files from this package directory and wraps them as
self-invoking functions for use with Playwright's page.evaluate().
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_JS_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def load_js(name: str) -> str:
    """Load a JS file from the js/ directory, wrapped as an IIFE.

    Args:
        name: Filename without extension (e.g. 'mutation_observer').

    Returns:
        JS source wrapped as `() => { ... }` for page.evaluate().
    """
    path = _JS_DIR / f"{name}.js"
    return path.read_text()
