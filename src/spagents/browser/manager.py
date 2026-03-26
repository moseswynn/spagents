"""Browser lifecycle management.

BrowserManager owns the Playwright browser instance and creates SPAPage
objects for browsing.
"""

from __future__ import annotations

from playwright.async_api import async_playwright, Browser, Playwright


class BrowserManager:
    """Manages a headless Chromium browser instance.

    Usage:
        async with BrowserManager() as manager:
            page = await manager.new_page()
            state = await page.goto("https://example.com")
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def __aenter__(self) -> BrowserManager:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def new_page(self) -> "SPAPage":
        """Create a new SPAPage with its own browser context."""
        from spagents.browser.page import SPAPage

        if not self._browser:
            raise RuntimeError("BrowserManager not started. Use 'async with'.")

        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        return SPAPage(page, context)

    async def new_session(self) -> "Session":
        """Create a new Session with its own browser context and page."""
        from spagents.browser.session import Session

        page = await self.new_page()
        return Session(page)
