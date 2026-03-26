"""Multi-signal content ready detection for SPAs.

Determines when a SPA has finished rendering meaningful content by combining:
- Network quiescence (no pending XHR/fetch requests)
- DOM mutation stabilization (MutationObserver sees no changes)
- Content presence heuristic (meaningful text exists, no loading indicators)
"""

from __future__ import annotations

import asyncio
import time

from playwright.async_api import Page

from spagents.extraction.models import ReadyResult
from spagents.js import load_js

_MUTATION_OBSERVER_JS = load_js("mutation_observer")
_CONTENT_HEURISTIC_JS = load_js("content_heuristic")

# Noise URL patterns to ignore when tracking network requests
_NOISE_PATTERNS = [
    "google-analytics.com",
    "googletagmanager.com",
    "facebook.net",
    "hotjar.com",
    "segment.io",
    "segment.com",
    "sentry.io",
    "newrelic.com",
    "doubleclick.net",
    "analytics",
    "tracking",
    "pixel",
    "/beacon",
]


def _is_noise_url(url: str) -> bool:
    """Check if a URL is analytics/tracking noise."""
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in _NOISE_PATTERNS)


class ContentReadyDetector:
    """Detects when a SPA has finished rendering meaningful content."""

    def __init__(
        self,
        timeout_ms: int = 15000,
        network_quiet_ms: int = 500,
        mutation_quiet_ms: int = 300,
        poll_interval_ms: int = 100,
    ):
        self.timeout_ms = timeout_ms
        self.network_quiet_ms = network_quiet_ms
        self.mutation_quiet_ms = mutation_quiet_ms
        self.poll_interval_ms = poll_interval_ms

    async def wait_until_ready(self, page: Page) -> ReadyResult:
        """Wait until the page has meaningful rendered content.

        Returns a ReadyResult indicating whether content is ready and which
        signals were satisfied.
        """
        start = time.monotonic()

        # Track in-flight network requests
        pending_requests: set[str] = set()
        last_network_activity = time.monotonic()

        def on_request(request):
            nonlocal last_network_activity
            url = request.url
            if not _is_noise_url(url):
                pending_requests.add(url)
                last_network_activity = time.monotonic()

        def on_request_done(request):
            nonlocal last_network_activity
            url = request.url
            pending_requests.discard(url)
            last_network_activity = time.monotonic()

        page.on("request", on_request)
        page.on("requestfinished", on_request_done)
        page.on("requestfailed", on_request_done)

        # Inject MutationObserver
        try:
            await page.evaluate(_MUTATION_OBSERVER_JS)
        except Exception:
            pass  # page might not have body yet

        signals = {
            "network_quiet": False,
            "dom_stable": False,
            "content_present": False,
        }

        deadline = start + (self.timeout_ms / 1000)

        while time.monotonic() < deadline:
            elapsed_since_network = (
                time.monotonic() - last_network_activity
            ) * 1000
            network_quiet = (
                len(pending_requests) == 0
                and elapsed_since_network >= self.network_quiet_ms
            )
            signals["network_quiet"] = network_quiet

            # Check DOM mutation stability
            try:
                last_mutation_ts = await page.evaluate(
                    "() => window.__spagents_last_mutation_ts || 0"
                )
                now_ts = await page.evaluate("() => Date.now()")
                mutation_gap = now_ts - last_mutation_ts
                mutation_count = await page.evaluate(
                    "() => window.__spagents_mutation_count || 0"
                )
                dom_stable = (
                    mutation_count > 0
                    and mutation_gap >= self.mutation_quiet_ms
                )
                signals["dom_stable"] = dom_stable
            except Exception:
                # Re-inject observer if page navigated
                try:
                    await page.evaluate(_MUTATION_OBSERVER_JS)
                except Exception:
                    pass
                dom_stable = False

            # Check content heuristic
            if network_quiet and dom_stable:
                try:
                    result = await page.evaluate(_CONTENT_HEURISTIC_JS)
                    signals["content_present"] = result.get(
                        "has_content", False
                    )
                except Exception:
                    signals["content_present"] = False

            if all(signals.values()):
                elapsed_ms = (time.monotonic() - start) * 1000
                return ReadyResult(
                    ready=True, elapsed_ms=elapsed_ms, signals=signals
                )

            await asyncio.sleep(self.poll_interval_ms / 1000)

        # Timeout — do a final content check anyway
        try:
            result = await page.evaluate(_CONTENT_HEURISTIC_JS)
            signals["content_present"] = result.get("has_content", False)
        except Exception:
            pass

        elapsed_ms = (time.monotonic() - start) * 1000
        return ReadyResult(
            ready=signals.get("content_present", False),
            elapsed_ms=elapsed_ms,
            signals=signals,
        )
