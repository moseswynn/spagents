"""Content extraction from rendered SPA pages.

Uses structural heuristics to extract articles, text, and links from
fully rendered pages. Handles both collapsed (list) and expanded (detail)
article views.
"""

from __future__ import annotations

from playwright.async_api import Page

from spagents.extraction.models import (
    Article,
    ExtractedContent,
    Highlight,
    Link,
    Perspective,
    Section,
    Source,
)
from spagents.js import load_js

_EXTRACT_ARTICLES_JS = load_js("extract_articles")
_EXTRACT_LINKS_JS = load_js("extract_links")
_EXTRACT_METADATA_JS = load_js("extract_metadata")
_EXTRACT_MAIN_TEXT_JS = load_js("extract_main_text")


class ContentExtractor:
    """Extracts structured content from a rendered page."""

    async def extract(self, page: Page) -> ExtractedContent:
        """Extract all structured content from the current page state."""
        title = await page.title()
        url = page.url

        articles_raw = await self._safe_evaluate(page, _EXTRACT_ARTICLES_JS, [])
        links_raw = await self._safe_evaluate(page, _EXTRACT_LINKS_JS, [])
        metadata = await self._safe_evaluate(page, _EXTRACT_METADATA_JS, {})
        main_text = await self._safe_evaluate(page, _EXTRACT_MAIN_TEXT_JS, "")

        articles = []
        for a in articles_raw:
            if not a.get("headline"):
                continue
            articles.append(Article(
                headline=a.get("headline", ""),
                category=a.get("category", ""),
                summary=a.get("summary"),
                url=a.get("url"),
                source=a.get("source"),
                location=a.get("location", ""),
                expanded=a.get("expanded", False),
                sources=[Source(**s) for s in a.get("sources", [])],
                highlights=[Highlight(**h) for h in a.get("highlights", [])],
                perspectives=[Perspective(**p) for p in a.get("perspectives", [])],
                quotes=a.get("quotes", []),
                sections=[Section(**s) for s in a.get("sections", [])],
                images=a.get("images", []),
            ))

        links = [
            Link(
                text=l.get("text", ""),
                url=l.get("url", ""),
                context=l.get("context", ""),
            )
            for l in links_raw
            if l.get("url")
        ]

        return ExtractedContent(
            title=title,
            url=url,
            main_text=main_text,
            articles=articles,
            links=links,
            metadata=metadata,
        )

    async def _safe_evaluate(self, page: Page, js: str, default):
        """Evaluate JS with a fallback default on error."""
        try:
            return await page.evaluate(js)
        except Exception:
            return default
