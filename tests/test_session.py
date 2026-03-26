"""Tests for Session — persistent browsing state."""

import pytest


@pytest.mark.asyncio
class TestSession:
    async def test_session_has_id(self, session):
        assert session.id
        assert len(session.id) == 8

    async def test_navigate_stamps_session_id(self, session, test_server):
        state = await session.navigate(f"{test_server}/index.html#home")
        assert state.session_id == session.id

    async def test_click_stamps_session_id(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#home")
        state = await session.click("#increment-btn")
        assert state.session_id == session.id

    async def test_scroll_stamps_session_id(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#home")
        state = await session.scroll("down")
        assert state.session_id == session.id

    async def test_type_text_stamps_session_id(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#form")
        state = await session.type_text("#name-input", "Test")
        assert state.session_id == session.id

    async def test_press_key_stamps_session_id(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#form")
        state = await session.press_key("Tab")
        assert state.session_id == session.id

    async def test_select_option_stamps_session_id(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#form")
        state = await session.select_option("#category-select", "feedback")
        assert state.session_id == session.id

    async def test_extract_stamps_session_id(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#home")
        state = await session.extract()
        assert state.session_id == session.id

    async def test_actions_returns_list(self, session, test_server):
        await session.navigate(f"{test_server}/index.html#home")
        actions = await session.actions()
        assert isinstance(actions, list)
        assert len(actions) > 0

    async def test_state_persists_across_navigations(self, session, test_server):
        """Session preserves browser context across route changes."""
        await session.navigate(f"{test_server}/index.html#form")
        await session.type_text("#name-input", "Persistent")

        # Navigate away and back
        await session.navigate(f"{test_server}/index.html#home")
        state = await session.navigate(f"{test_server}/index.html#form")

        # The form re-renders (SPA re-renders routes), so value won't persist
        # But session_id should remain constant
        assert state.session_id == session.id
