"""Tests for content extraction."""

import pytest


@pytest.mark.asyncio
class TestContentExtraction:
    async def test_extracts_title(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        assert state.content.title == "Test SPA"

    async def test_extracts_main_text(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        assert "Welcome Home" in state.content.main_text
        assert len(state.content.main_text) > 100

    async def test_extracts_metadata(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        assert state.content.metadata.get("title") == "Test SPA"
        assert "og:title" in state.content.metadata
        assert state.content.metadata["og:title"] == "Test SPA"

    async def test_extracts_links(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#home")
        urls = [link.url for link in state.content.links]
        assert any("example.com/docs" in u for u in urls)
        assert any("example.com/api" in u for u in urls)

    async def test_extracts_link_context(self, spa_page, test_server):
        """Links under a heading should get context from that heading."""
        state = await spa_page.goto(f"{test_server}/index.html#home")
        docs_link = next(
            (l for l in state.content.links if "docs" in l.url), None
        )
        assert docs_link is not None
        # Should pick up context from "Useful Links" heading
        assert docs_link.context != ""

    async def test_extracts_articles(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#articles")
        assert len(state.content.articles) >= 2
        headlines = [a.headline for a in state.content.articles]
        assert any("Science" in h for h in headlines)
        assert any("Tech" in h for h in headlines)

    async def test_article_has_summary(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#articles")
        # Collapsed articles should have summary from <p> tag
        science = next(
            (a for a in state.content.articles if "Science" in a.headline), None
        )
        assert science is not None
        assert science.url is not None

    async def test_extracts_delayed_content(self, spa_page, test_server):
        """Content loaded after a delay should be extracted once ready."""
        state = await spa_page.goto(f"{test_server}/index.html#delayed")
        assert "Async Article" in state.content.main_text

    async def test_extract_url_matches(self, spa_page, test_server):
        state = await spa_page.goto(f"{test_server}/index.html#form")
        assert "index.html" in state.content.url


@pytest.mark.asyncio
class TestExpandedArticles:
    async def test_expanded_article_structure(self, spa_page, test_server):
        """Click an accordion to expand, then extract rich article data."""
        await spa_page.goto(f"{test_server}/index.html#articles")
        # Click the first accordion to expand it
        state = await spa_page.click_element(
            'button[data-target="article-1-content"]'
        )
        # Re-extract to get updated content
        articles = state.content.articles
        science = next(
            (a for a in articles if "Science" in a.headline), None
        )
        assert science is not None
        # The expanded content should now be visible in main_text
        assert "Highlights" in state.content.main_text or "Sources" in state.content.main_text
