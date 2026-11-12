"""Beike parser entry point; real-site calibration requires authorized samples."""

import re
from urllib.parse import urlsplit

from app.collectors.parser import ParseResult, parse_generic_listing_html
from app.collectors.url_policy import check_source_url


def extract_source_id(source_url: str) -> str | None:
    path = urlsplit(check_source_url('beike', source_url)).path
    match = re.search(r'/ershoufang/([0-9]{8,220})\.html(?:/|$)', path, flags=re.IGNORECASE)
    return match.group(1) if match else None


def parse_listing_html(source_url: str, html: str) -> ParseResult:
    return parse_generic_listing_html(source_url, html, extract_source_id)
