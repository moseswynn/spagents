"""Tests for content ready detection."""

import pytest


@pytest.mark.asyncio
class TestContentReadyDetector:
    async def test_detects_ready_on_static_page(self, spa_page, test_server):
        """Home page has content immediately — should detect ready quickly."""
        state = await spa_page.goto(f"{test_server}/index.html#home")
        assert state.content_ready is True

    async def test_detects_ready_after_delayed_load(self, spa_page, test_server):
        """Delayed page loads content after 500ms — detector should wait for it."""
        state = await spa_page.goto(f"{test_server}/index.html#delayed")
        assert state.content_ready is True
        # The delayed content should be present
        assert "simulated API call" in state.content.main_text

    async def test_reports_signals(self, spa_page, test_server):
        """Page state should include content_ready flag."""
        state = await spa_page.goto(f"{test_server}/index.html#home")
        assert isinstance(state.content_ready, bool)

    async def test_handles_client_side_navigation(self, spa_page, test_server):
        """Navigate between routes and detect content on each."""
        await spa_page.goto(f"{test_server}/index.html#home")
        state = await spa_page.goto(f"{test_server}/index.html#articles")
        assert state.content_ready is True
        assert "Articles" in state.content.main_text
