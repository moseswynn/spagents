"""Tests for SPAPage interaction methods."""

import pytest


@pytest.mark.asyncio
class TestSPAPageNavigation:
    async def test_goto_returns_page_state(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        assert state.url.endswith("#home") or "index.html" in state.url
        assert state.title == "Test SPA"
        assert state.content is not None
        assert state.actions is not None

    async def test_goto_different_routes(self, spa_page, test_server):
        state1 = await spa_page.goto(f"{test_server}/index.html#home")
        assert "Welcome Home" in state1.content.main_text

        state2 = await spa_page.goto(f"{test_server}/index.html#articles")
        assert "Articles" in state2.content.main_text

        state3 = await spa_page.goto(f"{test_server}/index.html#form")
        assert "Contact Form" in state3.content.main_text

    async def test_url_property(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        assert "index.html" in spa_page.url


@pytest.mark.asyncio
class TestSPAPageClick:
    async def test_click_button(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        state = await spa_page.click_element("#increment-btn")
        assert "Count: 1" in state.content.main_text

    async def test_click_multiple_times(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        await spa_page.click_element("#increment-btn")
        await spa_page.click_element("#increment-btn")
        state = await spa_page.click_element("#increment-btn")
        assert "Count: 3" in state.content.main_text

    async def test_click_accordion(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#articles")
        state = await spa_page.click_element(
            'button[data-target="article-1-content"]'
        )
        # Expanded content should now be visible
        assert "Highlights" in state.content.main_text or "Sources" in state.content.main_text

    async def test_click_tab(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        state = await spa_page.click_element("#tab-two")
        assert "Content for tab two" in state.content.main_text


@pytest.mark.asyncio
class TestSPAPageInput:
    async def test_type_text(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#form")
        state = await spa_page.type_text("#name-input", "Alice")
        # Verify the value was set
        value = await spa_page._page.input_value("#name-input")
        assert value == "Alice"

    async def test_type_text_clear(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#form")
        await spa_page.type_text("#name-input", "Alice")
        await spa_page.type_text("#name-input", "Bob", clear=True)
        value = await spa_page._page.input_value("#name-input")
        assert value == "Bob"

    async def test_type_text_append(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#form")
        await spa_page.type_text("#name-input", "Hello")
        await spa_page.type_text("#name-input", " World", clear=False)
        value = await spa_page._page.input_value("#name-input")
        assert value == "Hello World"

    async def test_select_option(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#form")
        state = await spa_page.select_option("#category-select", "support")
        value = await spa_page._page.input_value("#category-select")
        assert value == "support"

    async def test_press_key(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#form")
        await spa_page.type_text("#name-input", "Test User")
        # Press Tab to move focus
        state = await spa_page.press_key("Tab")
        assert state is not None


@pytest.mark.asyncio
class TestSPAPageScroll:
    async def test_scroll_down(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        state = await spa_page.scroll_down()
        assert state is not None
        assert state.content_ready is True

    async def test_scroll_up(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        await spa_page.scroll_down()
        state = await spa_page.scroll_up()
        assert state is not None


@pytest.mark.asyncio
class TestSPAPageExtract:
    async def test_extract_without_navigation(self, spa_page, test_server):
        await spa_page.goto(f"{test_server}/index.html#home")
        state = await spa_page.extract()
        assert state.content.title == "Test SPA"
        assert "Welcome Home" in state.content.main_text
        assert state.content_ready is True
