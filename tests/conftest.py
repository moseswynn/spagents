"""Shared fixtures for spagents tests.

Provides a local HTTP server serving the test SPA, plus
browser/page/session fixtures built on BrowserManager.
"""

from __future__ import annotations

import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import pytest
import pytest_asyncio

from spagents.browser.manager import BrowserManager

_TEST_SPA_DIR = Path(__file__).parent / "test_spa"


# ── Local HTTP server ──────────────────────────────────────────────


class _QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler that suppresses request logging."""

    def log_message(self, format, *args):
        pass


def _start_server() -> tuple[HTTPServer, int]:
    handler = partial(_QuietHandler, directory=str(_TEST_SPA_DIR))
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


@pytest.fixture(scope="session")
def test_server():
    """Start a local HTTP server serving the test SPA for the session."""
    server, port = _start_server()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


# ── Browser fixtures ───────────────────────────────────────────────


@pytest_asyncio.fixture
async def browser_manager():
    """BrowserManager instance."""
    async with BrowserManager(headless=True) as mgr:
        yield mgr


@pytest_asyncio.fixture
async def spa_page(browser_manager):
    """Per-test SPAPage instance."""
    page = await browser_manager.new_page()
    yield page
    await page.close()


@pytest_asyncio.fixture
async def session(browser_manager):
    """Per-test Session instance."""
    sess = await browser_manager.new_session()
    yield sess
    await sess.close()
