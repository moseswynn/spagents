"""Tests for action discovery."""

import pytest

from spagents.extraction.models import AvailableAction


@pytest.mark.asyncio
class TestActionDiscovery:
    async def test_discovers_buttons(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        descs = [a.description for a in state.actions]
        assert any("Increment" in d for d in descs)
        assert any("Decrement" in d for d in descs)

    async def test_discovers_links(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        nav_actions = [a for a in state.actions if a.action_type == "navigate"]
        assert len(nav_actions) >= 2

    async def test_discovers_tabs(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        descs = [a.description for a in state.actions]
        assert any("Tab One" in d for d in descs)
        assert any("Tab Two" in d for d in descs)

    async def test_discovers_inputs(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#form")
        input_actions = [a for a in state.actions if a.action_type == "input"]
        assert len(input_actions) >= 3  # name, email, password, select, textarea

    async def test_input_has_placeholder_label(self, spa_page, test_server):
        """Input fields with no text should use placeholder as label."""
        state = await spa_page.goto(f"{test_server}/index.html#form")
        input_actions = [a for a in state.actions if a.action_type == "input"]
        labels = [a.element_text or "" for a in input_actions]
        assert any("name" in l.lower() for l in labels)
        assert any("email" in l.lower() for l in labels)

    async def test_discovers_clickable_divs(self, spa_page, test_server):
        """Divs with cursor:pointer or onclick should be discovered."""
        state = await spa_page.goto(f"{test_server}/index.html#home")
        descs = " ".join(a.description for a in state.actions)
        assert "clickable" in descs.lower() or "Click me" in descs or "Another clickable" in descs

    async def test_discovers_select_dropdown(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#form")
        select_actions = [
            a for a in state.actions
            if "select" in a.selector.lower() or "category" in (a.element_text or "").lower()
        ]
        assert len(select_actions) >= 1

    async def test_discovers_textarea(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#form")
        textarea_actions = [
            a for a in state.actions
            if "textarea" in a.selector.lower() or "message" in (a.element_text or "").lower()
        ]
        assert len(textarea_actions) >= 1

    async def test_discovers_tabindex_elements(self, spa_page, test_server):
        """Elements with tabindex should be discovered as interactive."""
        state = await spa_page.goto(f"{test_server}/index.html#home")
        descs = " ".join(a.description for a in state.actions)
        assert "clickable div" in descs.lower()

    async def test_action_selectors_are_valid(self, spa_page, test_server):
        """All discovered selectors should be queryable in the DOM."""
        state = await spa_page.goto(f"{test_server}/index.html#home")
        for action in state.actions:
            count = await spa_page._page.evaluate(
                "(sel) => document.querySelectorAll(sel).length",
                action.selector,
            )
            assert count >= 1, f"Selector {action.selector!r} matched 0 elements"

    async def test_discovers_dynamic_elements(self, spa_page, test_server):
        """Elements injected after delayed load should be discoverable."""
        state = await spa_page.goto(f"{test_server}/index.html#delayed")
        descs = [a.description for a in state.actions]
        assert any("Dynamic Button" in d for d in descs)
        # Dynamic input should also be found
        input_actions = [a for a in state.actions if a.action_type == "input"]
        labels = [a.element_text or "" for a in input_actions]
        assert any("dynamic" in l.lower() or "Dynamic" in l for l in labels)

    async def test_action_types_are_valid(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        valid_types = {"click", "input", "scroll", "navigate"}
        for action in state.actions:
            assert action.action_type in valid_types

    async def test_returns_available_action_models(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        for action in state.actions:
            assert isinstance(action, AvailableAction)
            assert action.selector
            assert action.description
