"""Pydantic contracts for operator-collected social media clues (Issue: social ingest).

These models define the external payload the browser userscript pushes and the
response the workbench consumes. They intentionally live beside the SQL table
in sql/015_social_posts.sql: the project has no ORM, so the table definition is
the storage model and these models are the transport/validation layer.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

PLATFORM_DOMAINS = {
    "xiaohongshu": ("xiaohongshu.com", "xhscin.com"),
    "douyin": ("douyin.com", "iesdouyin.com"),
    "channels": ("weixin.qq.com",),
}
MAX_CONTENT_CHARS = 50_000
MAX_HTML_SNIPPET_CHARS = 20_000
MAX_MEDIA_URLS = 20
MAX_TAGS = 20


class SocialPlatformEnum(str, Enum):
    xiaohongshu = "xiaohongshu"
    douyin = "douyin"
    channels = "channels"
    other = "other"


class SocialPostIngestPayload(BaseModel):
    """One operator-collected social post. Human-initiated, single-item capture."""

    platform: SocialPlatformEnum
    source_url: HttpUrl
    post_id: Optional[str] = Field(default=None, max_length=220)
    title: Optional[str] = Field(default=None, max_length=300)
    content: str = Field(min_length=1, max_length=MAX_CONTENT_CHARS)
    author_name: Optional[str] = Field(default=None, max_length=120)
    publish_time: Optional[str] = Field(default=None, max_length=64)
    media_urls: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    raw_html_snippet: Optional[str] = Field(default=None, max_length=MAX_HTML_SNIPPET_CHARS)

    @field_validator("content")
    @classmethod
    def content_must_have_visible_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped

    @field_validator("source_url")
    @classmethod
    def source_url_must_be_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("source_url must use https")
        return value

    @field_validator("media_urls")
    @classmethod
    def media_urls_must_be_http_lists(cls, value: List[str]) -> List[str]:
        if len(value) > MAX_MEDIA_URLS:
            raise ValueError(f"media_urls supports at most {MAX_MEDIA_URLS} entries")
        for item in value:
            if not item.startswith(("http://", "https://")):
                raise ValueError("media_urls entries must be http(s) URLs")
            if len(item) > 2000:
                raise ValueError("media_urls entries must not exceed 2000 characters")
        return value

    @field_validator("tags")
    @classmethod
    def tags_must_be_short_list(cls, value: List[str]) -> List[str]:
        if len(value) > MAX_TAGS:
            raise ValueError(f"tags supports at most {MAX_TAGS} entries")
        cleaned = []
        for item in value:
            stripped = item.strip()
            if not stripped:
                continue
            if len(stripped) > 40:
                raise ValueError("tags entries must not exceed 40 characters")
            cleaned.append(stripped)
        return cleaned

    @model_validator(mode="after")
    def source_url_matches_platform(self) -> "SocialPostIngestPayload":
        if self.platform is SocialPlatformEnum.other:
            return self
        host = (self.source_url.host or "").lower()
        domains = PLATFORM_DOMAINS[self.platform.value]
        if not any(host == domain or host.endswith("." + domain) for domain in domains):
            raise ValueError(
                f"source_url host {host} does not belong to platform {self.platform.value}")
        return self


class SocialIngestResponse(BaseModel):
    """Outcome of one ingest call: proof hash, clue labels and extracted hints."""

    status: Literal["stored", "duplicate"]
    id: str
    sha256: str
    is_ningbo_related: bool
    matched_keywords: List[str]
    hints: dict
