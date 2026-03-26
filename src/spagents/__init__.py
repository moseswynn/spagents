"""spagents — SPA-aware browsing library for AI agents."""

from spagents.browser.manager import BrowserManager
from spagents.browser.page import SPAPage
from spagents.browser.session import Session
from spagents.extraction.models import (
    Article,
    AvailableAction,
    ExtractedContent,
    Link,
    PageState,
)

__all__ = [
    "BrowserManager",
    "Session",
    "SPAPage",
    "Article",
    "AvailableAction",
    "ExtractedContent",
    "Link",
    "PageState",
]
