"""SPAPage — high-level wrapper around Playwright Page.

Orchestrates content ready detection, content extraction, and action
discovery to provide a simple interface for browsing SPAs.
"""

from __future__ import annotations

from playwright.async_api import BrowserContext, Page

from spagents.actions.discovery import ActionDiscovery
from spagents.detection.ready import ContentReadyDetector
from spagents.extraction.extractor import ContentExtractor
from spagents.extraction.models import PageState


class SPAPage:
    """A high-level page that waits for SPA content and extracts structured data."""

    def __init__(
        self,
        page: Page,
        context: BrowserContext,
        timeout_ms: int = 15000,
    ):
        self._page = page
        self._context = context
        self._detector = ContentReadyDetector(timeout_ms=timeout_ms)
        self._extractor = ContentExtractor()
        self._action_discovery = ActionDiscovery()

    @property
    def url(self) -> str:
        return self._page.url

    async def goto(self, url: str) -> PageState:
        """Navigate to a URL, wait for SPA content, and extract structured data."""
        await self._page.goto(url, wait_until="domcontentloaded")
        return await self._wait_and_extract()

    async def click_element(self, selector: str) -> PageState:
        """Click an element and wait for any resulting content changes."""
        await self._page.click(selector)
        return await self._wait_and_extract()

    async def scroll_down(self) -> PageState:
        """Scroll down one viewport height and wait for new content."""
        await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
        return await self._wait_and_extract()

    async def scroll_up(self) -> PageState:
        """Scroll up one viewport height and wait for new content."""
        await self._page.evaluate("window.scrollBy(0, -window.innerHeight)")
        return await self._wait_and_extract()

    async def type_text(self, selector: str, text: str, clear: bool = True) -> PageState:
        """Type text into an input element.

        Args:
            selector: CSS selector for the input element.
            text: Text to type.
            clear: If True, clear existing content before typing.
        """
        if clear:
            await self._page.fill(selector, text)
        else:
            await self._page.type(selector, text)
        return await self._wait_and_extract()

    async def press_key(self, key: str) -> PageState:
        """Press a keyboard key (e.g. 'Enter', 'Escape', 'Tab')."""
        await self._page.keyboard.press(key)
        return await self._wait_and_extract()

    async def select_option(self, selector: str, value: str) -> PageState:
        """Select an option from a <select> dropdown."""
        await self._page.select_option(selector, value)
        return await self._wait_and_extract()

    async def discover_actions(self) -> list:
        """Find all interactive elements on the current page."""
        return await self._action_discovery.discover(self._page)

    async def extract(self) -> PageState:
        """Re-extract content from the current page without navigating."""
        return await self._build_page_state(content_ready=True)

    async def close(self) -> None:
        """Close the page and its browser context."""
        await self._page.close()
        await self._context.close()

    async def _wait_and_extract(self) -> PageState:
        """Wait for content ready, then extract."""
        ready_result = await self._detector.wait_until_ready(self._page)
        return await self._build_page_state(
            content_ready=ready_result.ready,
        )

    async def _build_page_state(self, content_ready: bool) -> PageState:
        """Build a PageState from the current page."""
        content = await self._extractor.extract(self._page)
        actions = await self._action_discovery.discover(self._page)
        title = await self._page.title()

        return PageState(
            url=self._page.url,
            title=title,
            content=content,
            actions=actions,
            content_ready=content_ready,
        )
