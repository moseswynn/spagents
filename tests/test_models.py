"""Tests for Pydantic models."""

from spagents.extraction.models import (
    Article,
    AvailableAction,
    ExtractedContent,
    Highlight,
    Link,
    PageState,
    Perspective,
    ReadyResult,
    Section,
    Source,
)


class TestSource:
    def test_defaults(self):
        s = Source(name="Reuters")
        assert s.name == "Reuters"
        assert s.url == ""
        assert s.time_ago == ""
        assert s.article_count == 1

    def test_full(self):
        s = Source(name="AP", url="https://ap.com", time_ago="3h", article_count=5)
        assert s.article_count == 5


class TestArticle:
    def test_minimal(self):
        a = Article(headline="Test")
        assert a.headline == "Test"
        assert a.expanded is False
        assert a.sources == []
        assert a.highlights == []

    def test_expanded(self):
        a = Article(
            headline="Big Story",
            expanded=True,
            sources=[Source(name="AP")],
            highlights=[Highlight(title="Key", text="Details")],
            perspectives=[Perspective(speaker="Alice", text="Good")],
            sections=[Section(heading="Timeline", text="2024")],
            quotes=["Notable quote"],
            images=["caption.jpg"],
        )
        assert a.expanded is True
        assert len(a.sources) == 1
        assert len(a.highlights) == 1
        assert a.perspectives[0].speaker == "Alice"
        assert a.sections[0].heading == "Timeline"


class TestAvailableAction:
    def test_click(self):
        a = AvailableAction(
            selector="#btn", action_type="click", description="Button: Submit"
        )
        assert a.action_type == "click"

    def test_input(self):
        a = AvailableAction(
            selector="#email", action_type="input", description="Input: Email"
        )
        assert a.action_type == "input"

    def test_navigate(self):
        a = AvailableAction(
            selector="a", action_type="navigate", description="Navigate: Home"
        )
        assert a.action_type == "navigate"


class TestExtractedContent:
    def test_defaults(self):
        c = ExtractedContent()
        assert c.title == ""
        assert c.articles == []
        assert c.links == []
        assert c.metadata == {}

    def test_with_data(self):
        c = ExtractedContent(
            title="Page",
            url="https://example.com",
            main_text="Hello",
            articles=[Article(headline="A")],
            links=[Link(text="L", url="https://example.com/l")],
            metadata={"title": "Page"},
        )
        assert len(c.articles) == 1
        assert len(c.links) == 1


class TestReadyResult:
    def test_ready(self):
        r = ReadyResult(
            ready=True,
            elapsed_ms=150.0,
            signals={"network_quiet": True, "dom_stable": True, "content_present": True},
        )
        assert r.ready is True

    def test_not_ready(self):
        r = ReadyResult(ready=False, elapsed_ms=15000.0)
        assert r.ready is False


class TestPageState:
    def test_defaults(self):
        s = PageState(url="https://example.com", title="Example")
        assert s.session_id == ""
        assert s.content_ready is True
        assert s.actions == []

    def test_session_id_mutation(self):
        s = PageState(url="https://example.com", title="Example")
        s.session_id = "abc123"
        assert s.session_id == "abc123"
