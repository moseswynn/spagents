"""Tests for the JS file loader."""

from spagents.js import load_js


class TestJSLoader:
    def test_loads_mutation_observer(self):
        js = load_js("mutation_observer")
        assert "__spagents_observer" in js
        assert "MutationObserver" in js

    def test_loads_content_heuristic(self):
        js = load_js("content_heuristic")
        assert "has_content" in js

    def test_loads_extract_articles(self):
        js = load_js("extract_articles")
        assert "headline" in js

    def test_loads_extract_links(self):
        js = load_js("extract_links")
        assert "href" in js

    def test_loads_extract_metadata(self):
        js = load_js("extract_metadata")
        assert "og:" in js

    def test_loads_extract_main_text(self):
        js = load_js("extract_main_text")
        assert "innerText" in js

    def test_loads_discover_actions(self):
        js = load_js("discover_actions")
        assert "action_type" in js

    def test_caching(self):
        """Repeated calls return the same object (lru_cache)."""
        js1 = load_js("mutation_observer")
        js2 = load_js("mutation_observer")
        assert js1 is js2

    def test_invalid_file_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            load_js("nonexistent_file")
