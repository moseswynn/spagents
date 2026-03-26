"""Pydantic models for structured content extraction."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    """A source/publisher for an article."""

    name: str
    url: str = ""
    time_ago: str = ""  # e.g. "17h", "1d"
    article_count: int = 1


class Highlight(BaseModel):
    """A numbered highlight/key point from an expanded article."""

    title: str
    text: str


class Perspective(BaseModel):
    """A named perspective or viewpoint on a story."""

    speaker: str
    text: str


class Section(BaseModel):
    """A generic named section within an expanded article."""

    heading: str
    text: str


class Article(BaseModel):
    """A single article or content item extracted from a page."""

    headline: str
    category: str = ""
    summary: str | None = None
    url: str | None = None
    source: str | None = None
    location: str = ""
    expanded: bool = False
    sources: list[Source] = Field(default_factory=list)
    highlights: list[Highlight] = Field(default_factory=list)
    perspectives: list[Perspective] = Field(default_factory=list)
    quotes: list[str] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)  # image caption strings


class Link(BaseModel):
    """A meaningful link found on the page."""

    text: str
    url: str
    context: str = ""  # parent heading or section name


class AvailableAction(BaseModel):
    """An interactive element discovered on the page."""

    selector: str
    action_type: Literal["click", "input", "scroll", "navigate"]
    description: str
    element_text: str | None = None


class ExtractedContent(BaseModel):
    """Structured content extracted from a rendered page."""

    title: str = ""
    url: str = ""
    main_text: str = ""
    articles: list[Article] = Field(default_factory=list)
    links: list[Link] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReadyResult(BaseModel):
    """Result from the content ready detector."""

    ready: bool
    elapsed_ms: float
    signals: dict[str, bool] = Field(default_factory=dict)


class PageState(BaseModel):
    """Complete state of a browsed page, returned to the caller."""

    url: str
    title: str
    session_id: str = ""
    content: ExtractedContent = Field(default_factory=ExtractedContent)
    actions: list[AvailableAction] = Field(default_factory=list)
    content_ready: bool = True
