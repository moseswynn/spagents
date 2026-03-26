"""MCP server exposing spagents browsing capabilities as tools.

Enables any MCP-compatible AI agent to browse SPAs, interact with
elements, and extract structured content.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from spagents.browser.manager import BrowserManager
from spagents.browser.session import Session

# Global state — browser is lazily initialized on first use
_manager: BrowserManager | None = None
_sessions: dict[str, Session] = {}
_lock = asyncio.Lock()


async def _ensure_manager() -> BrowserManager:
    """Lazily initialize the browser manager."""
    global _manager
    if _manager is None:
        _manager = BrowserManager(headless=True)
        await _manager.__aenter__()
    return _manager


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Clean up browser on server shutdown."""
    global _manager
    try:
        yield
    finally:
        for session in _sessions.values():
            try:
                await session.close()
            except Exception:
                pass
        _sessions.clear()
        if _manager is not None:
            await _manager.__aexit__(None, None, None)
            _manager = None


mcp = FastMCP(
    "spagents",
    instructions=(
        "SPA-aware browsing tools for AI agents. Use 'browse' to navigate "
        "to a URL and get structured content. Use session_id from the "
        "response to interact further with click, type_text, scroll, etc."
    ),
    lifespan=lifespan,
)


async def _get_or_create_session(session_id: str | None = None) -> Session:
    """Get an existing session or create a new one."""
    async with _lock:
        if session_id and session_id in _sessions:
            return _sessions[session_id]
        manager = await _ensure_manager()
        session = await manager.new_session()
        _sessions[session.id] = session
        return session


def _state_to_dict(state) -> dict[str, Any]:
    """Convert PageState to a dict for MCP response."""
    return state.model_dump()


@mcp.tool()
async def browse(url: str, session_id: str | None = None) -> dict[str, Any]:
    """Navigate to a URL and return the fully rendered page content.

    Handles SPAs by executing JavaScript and waiting for content to render.
    Returns structured content including text, articles, links, and
    available interactive actions.

    If session_id is provided, reuses an existing browser session
    (preserving cookies and state). Otherwise creates a new session.
    """
    session = await _get_or_create_session(session_id)
    state = await session.navigate(url)
    return _state_to_dict(state)


@mcp.tool()
async def extract_content(session_id: str) -> dict[str, Any]:
    """Re-extract content from the current page in an existing session.

    Useful after interactions that change the page without navigating.
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    state = await session.extract()
    return _state_to_dict(state)


@mcp.tool()
async def click(session_id: str, selector: str) -> dict[str, Any]:
    """Click an element on the current page and return the updated state.

    Use list_actions first to discover available elements and their selectors.

    Args:
        session_id: The session to interact with.
        selector: CSS selector of the element to click.
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    state = await session.click(selector)
    return _state_to_dict(state)


@mcp.tool()
async def type_text(
    session_id: str, selector: str, text: str, clear: bool = True
) -> dict[str, Any]:
    """Type text into an input element on the current page.

    Use list_actions to find input elements and their selectors.

    Args:
        session_id: The session to interact with.
        selector: CSS selector of the input element.
        text: The text to type.
        clear: If True, clear existing content before typing.
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    state = await session.type_text(selector, text, clear=clear)
    return _state_to_dict(state)


@mcp.tool()
async def press_key(session_id: str, key: str) -> dict[str, Any]:
    """Press a keyboard key in the current page.

    Common keys: Enter, Escape, Tab, ArrowDown, ArrowUp, Backspace, Delete.

    Args:
        session_id: The session to interact with.
        key: The key to press (e.g. 'Enter', 'Escape', 'Tab').
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    state = await session.press_key(key)
    return _state_to_dict(state)


@mcp.tool()
async def list_actions(session_id: str) -> dict[str, Any]:
    """List all available interactive elements on the current page.

    Returns clickable links, buttons, inputs, navigation elements,
    and other interactive elements with their CSS selectors.
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    actions = await session.actions()
    return {
        "session_id": session_id,
        "url": session.page.url,
        "actions": [a.model_dump() for a in actions],
    }


@mcp.tool()
async def navigate(session_id: str, url: str) -> dict[str, Any]:
    """Navigate to a new URL within an existing session, preserving state.

    Cookies, localStorage, and auth state are preserved from the session.

    Args:
        session_id: The session to navigate.
        url: The URL to navigate to.
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    state = await session.navigate(url)
    return _state_to_dict(state)


@mcp.tool()
async def scroll(
    session_id: str, direction: str = "down"
) -> dict[str, Any]:
    """Scroll the page and return any newly loaded content.

    Many SPAs implement infinite scroll — this triggers it and extracts
    new items.

    Args:
        session_id: The session to scroll.
        direction: 'down' or 'up'.
    """
    async with _lock:
        session = _sessions.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    state = await session.scroll(direction)
    return _state_to_dict(state)


@mcp.tool()
async def close_session(session_id: str) -> dict[str, Any]:
    """Close a browser session and free its resources.

    Args:
        session_id: The session to close.
    """
    async with _lock:
        session = _sessions.pop(session_id, None)
    if not session:
        return {"error": f"Session {session_id} not found"}
    await session.close()
    return {"status": "closed", "session_id": session_id}
