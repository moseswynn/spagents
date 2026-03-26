"""Action discovery — find interactive elements on a rendered page.

Scans the DOM for ALL interactive elements including:
- Standard: <a>, <button>, <input>, <select>, <textarea>
- ARIA roles: [role="button"], [role="tab"], [role="listitem"], etc.
- Cursor-based: elements with cursor:pointer
- Tabindex: elements with explicit tabindex
- Event-based: elements with onclick attributes
"""

from __future__ import annotations

from playwright.async_api import Page

from spagents.extraction.models import AvailableAction
from spagents.js import load_js

_DISCOVER_ACTIONS_JS = load_js("discover_actions")


class ActionDiscovery:
    """Discovers interactive elements on a rendered page."""

    async def discover(self, page: Page) -> list[AvailableAction]:
        """Find all interactive elements on the current page."""
        try:
            raw = await page.evaluate(_DISCOVER_ACTIONS_JS)
        except Exception:
            return []

        return [
            AvailableAction(
                selector=a["selector"],
                action_type=a["action_type"],
                description=a["description"],
                element_text=a.get("element_text"),
            )
            for a in raw
            if a.get("selector")
        ]
