"""API contracts for public-page samples and source policy review."""
from datetime import datetime
from decimal import Decimal
import re
from typing import Literal
from pydantic import Field, StrictBool, StrictInt, ValidationInfo, field_validator, model_validator
from app.models import DatabaseTextSafeModel, _normalize_numeric_storage_scale
from app.collectors.url_policy import source_page_key


class HTMLPageIn(DatabaseTextSafeModel):
    source: Literal['beike', 'anjuke']
    source_url: str = Field(min_length=12, max_length=2000)
    html: str = Field(min_length=20, max_length=1_000_000)
    captured_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)

    @field_validator('captured_at')
    @classmethod
    def timezone_required(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError('captured_at must include a timezone')
        return value

    @field_validator('html')
    @classmethod
    def html_byte_limit(cls, value):
        try:
            size = len(value.encode('utf-8'))
        except UnicodeEncodeError as exc:
            raise ValueError('html must be valid UTF-8 text') from exc
        if size > 1_000_000:
            raise ValueError('html must not exceed 1000000 UTF-8 bytes')
        return value


class CollectionTargetIn(DatabaseTextSafeModel):
    source: Literal['beike', 'anjuke']
    url: str = Field(min_length=12, max_length=2000)
    enabled: StrictBool = False
    poll_interval_minutes: int = Field(default=1440, ge=360, le=10080)


class CollectionTargetPatch(DatabaseTextSafeModel):
    enabled: StrictBool | None = None
    poll_interval_minutes: int | None = Field(default=None, ge=360, le=10080)


class DiscoveryStateIn(DatabaseTextSafeModel):
    version: Literal[1] = 1
    revision: StrictInt = Field(ge=0)
    source: Literal['beike', 'anjuke']
    seen_ids: list[str] = Field(default_factory=list, max_length=100_000)
    last_page_url: str | None = Field(default=None, max_length=2000)
    next_page_url: str | None = Field(default=None, max_length=2000)
    visited_page_urls: list[str] = Field(default_factory=list, max_length=100_000)
    last_attempted_page_url: str | None = Field(default=None, max_length=2000)
    last_error_type: str | None = Field(default=None, max_length=80)
    failed_attempts: StrictInt = Field(default=0, ge=0)
    sweep_number: StrictInt = Field(default=0, ge=0)
    sweep_active: StrictBool = False
    sweep_seen_ids: list[str] = Field(default_factory=list, max_length=100_000)
    completed_sweeps: StrictInt = Field(default=0, ge=0)

    @field_validator('seen_ids')
    @classmethod
    def deduplicate_seen_ids(cls, values):
        return list(dict.fromkeys(values))

    @field_validator('sweep_seen_ids')
    @classmethod
    def deduplicate_sweep_seen_ids(cls, values):
        return list(dict.fromkeys(values))

    @field_validator('visited_page_urls')
    @classmethod
    def deduplicate_visited_pages(cls, values):
        return list(dict.fromkeys(values))

    @model_validator(mode='after')
    def validate_source_ids_and_error_type(self):
        minimum_length = 8 if self.source == 'beike' else 7
        pattern = re.compile(rf'[0-9]{{{minimum_length},220}}')
        if any(not pattern.fullmatch(value) for value in (*self.seen_ids, *self.sweep_seen_ids)):
            raise ValueError('discovery state contains an invalid listing ID for source')
        if (self.next_page_url is not None and self.last_page_url is not None
                and source_page_key(self.source, self.next_page_url)
                == source_page_key(self.source, self.last_page_url)):
            raise ValueError('next_page_url must not repeat last_page_url')
        if (self.last_error_type is not None
                and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', self.last_error_type)):
            raise ValueError('last_error_type must be an error type name')
        return self


class DiscoveryReviewIn(DatabaseTextSafeModel):
    conclusion: Literal['still_listed', 'confirmed_withdrawn', 'inconclusive']
    note: str | None = Field(default=None, max_length=1000)

    @field_validator('note', mode='before')
    @classmethod
    def normalize_note(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class PolicyReviewIn(DatabaseTextSafeModel):
    online_policy_status: Literal['not_reviewed', 'not_authorized', 'approved', 'revoked']
    online_enabled: StrictBool = False
    policy_reference: str | None = Field(default=None, max_length=1000)
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode='after')
    def requires_evidence(self):
        if (self.online_policy_status == 'approved'
                and not (self.policy_reference or '').strip()):
            raise ValueError('Approved policy requires a non-empty permission reference')
        if self.online_enabled and self.online_policy_status != 'approved':
            raise ValueError('Enabling online collection requires approved status and permission evidence')
        return self


class CandidateCorrection(DatabaseTextSafeModel):
    source_listing_id: str | None = Field(default=None, min_length=7, max_length=220,
                                                 pattern=r'^[0-9]{7,220}$')
    title: str | None = Field(default=None, min_length=1, max_length=500)
    community_name: str | None = Field(default=None, min_length=2, max_length=180)
    district: str | None = Field(default=None, max_length=100)
    area_sqm: Decimal | None = Field(default=None, gt=0, le=20000)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    floor_text: str | None = Field(default=None, max_length=120)
    decoration: str | None = Field(default=None, max_length=120)
    asking_price_wan: Decimal | None = Field(default=None, gt=0, le=200000)
    review_note: str = Field(min_length=5, max_length=1000)

    @field_validator('bedrooms', mode='before')
    @classmethod
    def reject_boolean_bedroom_count(cls, value):
        if isinstance(value, bool):
            raise ValueError('bedrooms must be an integer, not a boolean')
        return value

    @field_validator('source_listing_id', 'title', 'community_name', 'district',
                     'floor_text', 'decoration', 'review_note', mode='before')
    @classmethod
    def trim_nonblank_text(cls, value, info: ValidationInfo):
        if value is None or not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            raise ValueError(f'{info.field_name} must not be blank')
        return value

    @field_validator('area_sqm', 'asking_price_wan')
    @classmethod
    def database_numeric_scale(cls, value: Decimal | None):
        return _normalize_numeric_storage_scale(value)
