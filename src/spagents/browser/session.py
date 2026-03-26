"""Session — persistent browsing state across navigations.

A Session wraps a BrowserContext and SPAPage, preserving cookies,
localStorage, and auth state across navigations within the same SPA.
"""

from __future__ import annotations

import uuid

from spagents.browser.page import SPAPage
from spagents.extraction.models import AvailableAction, PageState


class Session:
    """A persistent browsing session with state preservation."""

    def __init__(self, page: SPAPage):
        self.id: str = str(uuid.uuid4())[:8]
        self.page: SPAPage = page

    async def navigate(self, url: str) -> PageState:
        """Navigate to a URL within this session."""
        state = await self.page.goto(url)
        state.session_id = self.id
        return state

    async def click(self, selector: str) -> PageState:
        """Click an element and return updated page state."""
        state = await self.page.click_element(selector)
        state.session_id = self.id
        return state

    async def scroll(self, direction: str = "down") -> PageState:
        """Scroll the page and return updated state."""
        if direction == "up":
            state = await self.page.scroll_up()
        else:
            state = await self.page.scroll_down()
        state.session_id = self.id
        return state

    async def type_text(self, selector: str, text: str, clear: bool = True) -> PageState:
        """Type text into an input element."""
        state = await self.page.type_text(selector, text, clear=clear)
        state.session_id = self.id
        return state

    async def press_key(self, key: str) -> PageState:
        """Press a keyboard key (e.g. 'Enter', 'Escape', 'Tab')."""
        state = await self.page.press_key(key)
        state.session_id = self.id
        return state

    async def select_option(self, selector: str, value: str) -> PageState:
        """Select an option from a dropdown."""
        state = await self.page.select_option(selector, value)
        state.session_id = self.id
        return state

    async def extract(self) -> PageState:
        """Re-extract content from the current page."""
        state = await self.page.extract()
        state.session_id = self.id
        return state

    async def actions(self) -> list[AvailableAction]:
        """List available interactive elements."""
        return await self.page.discover_actions()

    async def close(self) -> None:
        """Close this session and free resources."""
        await self.page.close()
