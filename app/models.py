from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, StrictBool, ValidationInfo, field_validator, model_validator


def _normalize_numeric_storage_scale(value: Decimal | None):
    if value is None:
        return value
    try:
        normalized = value.quantize(Decimal('0.01'))
    except InvalidOperation as exc:
        raise ValueError('Numeric values must fit database precision of two decimal places') from exc
    if normalized != value:
        raise ValueError('Numeric values must fit database precision of two decimal places')
    return normalized


def _contains_nul(value) -> bool:
    if isinstance(value, str):
        return '\x00' in value
    if isinstance(value, dict):
        return any(_contains_nul(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_nul(item) for item in value)
    return False


class DatabaseTextSafeModel(BaseModel):
    @model_validator(mode='before')
    @classmethod
    def reject_nul_in_persisted_text(cls, value):
        if _contains_nul(value):
            raise ValueError('Text values must not contain a NUL character')
        return value


class AccountIn(DatabaseTextSafeModel):
    platform: Literal['douyin', 'wechat_channels']
    account_ref: str = Field(min_length=2, max_length=500)
    nickname: str | None = Field(default=None, max_length=160)
    history_mode: Literal['none', '30d', '90d'] = 'none'
    poll_interval_minutes: int = Field(default=120, ge=60, le=10080)

    @field_validator('account_ref', mode='before')
    @classmethod
    def clean_ref(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError('account_ref must not be blank')
        return value

    @model_validator(mode='after')
    def check_douyin_ref(self):
        if self.platform == 'douyin' and (
                '://' in self.account_ref or self.account_ref.lower().startswith('http')):
            from urllib.parse import urlsplit, urlunsplit
            if any(char.isspace() or ord(char) < 0x20 or 0x7f <= ord(char) <= 0x9f
                   for char in self.account_ref):
                raise ValueError('Douyin profile link must not contain whitespace or controls')
            try:
                parsed = urlsplit(self.account_ref)
                port = parsed.port
            except ValueError as exc:
                raise ValueError('Douyin profile link is malformed') from exc
            host = (parsed.hostname or '').lower()
            if (parsed.scheme.lower() != 'https'
                    or not (host == 'douyin.com' or host.endswith('.douyin.com'))
                    or parsed.username is not None or parsed.password is not None
                    or port not in (None, 443)):
                raise ValueError('Douyin profile link must be an HTTPS douyin.com URL')
            if '?' in self.account_ref or '#' in self.account_ref:
                self.account_ref = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
        return self


class AccountPatch(DatabaseTextSafeModel):
    nickname: str | None = Field(default=None, max_length=160)
    enabled: StrictBool | None = None
    history_mode: Literal['none', '30d', '90d'] | None = None
    poll_interval_minutes: int | None = Field(default=None, ge=60, le=10080)


class VideoIn(DatabaseTextSafeModel):
    platform: Literal['douyin', 'wechat_channels']
    source_post_id: str = Field(min_length=1, max_length=220)
    account_id: UUID | None = None
    source_url: str | None = Field(default=None, max_length=2000)
    author_name: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=2000)
    description: str | None = None
    published_at: datetime | None = None
    raw_location: str | None = Field(default=None, max_length=300)
    permission_note: str | None = Field(default=None, max_length=400)
    transcript: str | None = None
    ocr_text: str | None = None

    @field_validator('source_post_id', mode='before')
    @classmethod
    def normalize_source_post_id(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError('source_post_id must not be blank')
        return value


class VideoEnrichment(DatabaseTextSafeModel):
    transcript: str | None = None
    ocr_text: str | None = None
    raw_location: str | None = None


class CommunityIn(DatabaseTextSafeModel):
    name: str = Field(min_length=2, max_length=180)
    district: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=300)
    aliases: list[str] = Field(default_factory=list, max_length=30)
    verified: StrictBool = False

    @field_validator('name', mode='before')
    @classmethod
    def normalize_community_name(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError('name must not be blank')
        return value


class ListingIn(DatabaseTextSafeModel):
    source: Literal['beike', 'anjuke', 'agent', 'other']
    source_listing_id: str = Field(min_length=1, max_length=220)
    title: str | None = Field(default=None, max_length=1000)
    listing_url: str | None = Field(default=None, max_length=2000)
    community_name: str = Field(min_length=2, max_length=180)
    district: str | None = Field(default=None, max_length=100)
    area_sqm: Decimal = Field(gt=0, le=20000)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    floor_text: str | None = Field(default=None, max_length=120)
    decoration: str | None = Field(default=None, max_length=120)
    asking_price_wan: Decimal = Field(gt=0, le=200000)
    observed_at: datetime | None = None
    permission_note: str | None = Field(default=None, max_length=400)

    @field_validator('bedrooms', mode='before')
    @classmethod
    def reject_boolean_bedroom_count(cls, value):
        if isinstance(value, bool):
            raise ValueError('bedrooms must be an integer, not a boolean')
        return value

    @field_validator('community_name', mode='before')
    @classmethod
    def normalize_community_name(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError('community_name must not be blank')
        return value

    @field_validator('title', 'listing_url', 'district', 'floor_text', 'decoration',
                     'permission_note', mode='before')
    @classmethod
    def normalize_optional_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator('area_sqm', 'asking_price_wan')
    @classmethod
    def database_numeric_scale(cls, value: Decimal):
        return _normalize_numeric_storage_scale(value)

    @field_validator('source_listing_id', mode='before')
    @classmethod
    def normalize_source_listing_id(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError('source_listing_id must not be blank')
        return value

    @field_validator('source_listing_id')
    @classmethod
    def source_listing_id_matches_source(cls, value: str, info: ValidationInfo):
        source = info.data.get('source')
        if source not in ('beike', 'anjuke'):
            return value
        minimum_length = 8 if source == 'beike' else 7
        if (not value.isascii() or not value.isdigit()
                or not minimum_length <= len(value) <= 220):
            raise ValueError('source_listing_id does not match source ID format')
        return value


class SavedSearchIn(DatabaseTextSafeModel):
    name: str = Field(min_length=1, max_length=120)
    district: str | None = Field(default=None, max_length=100)
    districts: list[str] = Field(default_factory=list, max_length=10)
    community_name: str | None = Field(default=None, max_length=180)
    preferred_communities: list[str] = Field(default_factory=list, max_length=30)
    excluded_communities: list[str] = Field(default_factory=list, max_length=30)
    max_price_wan: Decimal | None = Field(default=None, gt=0)
    min_area_sqm: Decimal | None = Field(default=None, gt=0)
    min_bedrooms: int | None = Field(default=None, ge=0, le=20)
    max_listing_age_days: int | None = Field(default=None, ge=1, le=3650)
    min_drop_pct: Decimal = Field(default=Decimal('5'), ge=0, le=100)
    notifications_enabled: StrictBool = True

    @field_validator('min_bedrooms', 'max_listing_age_days', mode='before')
    @classmethod
    def reject_boolean_search_integer(cls, value, info: ValidationInfo):
        if isinstance(value, bool):
            raise ValueError(f'{info.field_name} must be an integer, not a boolean')
        return value

    @field_validator('name', mode='before')
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError('name must not be blank')
        return value

    @field_validator('district', 'community_name', mode='before')
    @classmethod
    def normalize_optional_text_filters(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator('districts', 'preferred_communities', 'excluded_communities')
    @classmethod
    def clean_names(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    @field_validator('max_price_wan', 'min_area_sqm', 'min_drop_pct')
    @classmethod
    def database_numeric_scale(cls, value: Decimal | None):
        return _normalize_numeric_storage_scale(value)


class VideoBatch(DatabaseTextSafeModel):
    items: list[VideoIn] = Field(min_length=1, max_length=200)
