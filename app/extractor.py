"""Conservative keyword helper, not a valuation model or validated fact extractor."""
import re

AREA_RE = re.compile(r'(?<!\d)(\d{2,4}(?:\.\d{1,2})?)\s*(?:㎡|m²|平米|平方(?:米)?)')
PRICE_RE = re.compile(r'(?<!\d)(\d{2,5}(?:\.\d{1,2})?)\s*万(?:元)?')
ROOM_RE = re.compile(r'(?<![0-9一二三四五六七八九十百零两])([1-9一二三四五六七八九两])\s*(?:室|房)')
ROOM_NUMERALS = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
                 '七': 7, '八': 8, '九': 9, '两': 2}
DISTRICTS = ('鄞州', '海曙', '江北', '镇海', '北仑', '奉化', '余姚', '慈溪', '宁海', '象山')


def extract_hints(*parts: str | None, known_community_names: list[str] | None = None,
                  source_labels: list[str] | None = None) -> dict:
    sources = [
        (source_labels[i] if source_labels and i < len(source_labels) else f'part_{i + 1}', str(part))
        for i, part in enumerate(parts) if part
    ]
    text = '\n'.join(value for _, value in sources)
    source_spans = []
    offset = 0
    for source, value in sources:
        source_spans.append((offset, offset + len(value), source))
        offset += len(value) + 1

    def find_in_source(value):
        for left, right, _ in source_spans:
            start = text[left:right].find(value)
            if start >= 0:
                return left + start
        return None

    def evidence(field, value, start, end):
        span = next(((left, right, name) for left, right, name in source_spans
                     if left <= start and end <= right), None)
        if span is None:
            return None
        left, _, source = span
        return {'field': field, 'value': value, 'source': source, 'quote': text[start:end],
                'start_char': start - left, 'end_char': end - left}

    evidence_items = []

    def numeric_mentions(pattern, field, convert, minimum=None, maximum=None):
        values = []
        for match in pattern.finditer(text):
            value = convert(match.group(1))
            if minimum is not None and not minimum <= value <= maximum:
                continue
            if value not in values:
                values.append(value)
                item = evidence(field, value, match.start(), match.end())
                if item:
                    evidence_items.append(item)
        return values

    price_candidates = numeric_mentions(PRICE_RE, 'price_mentions_wan', float, 5, 200000)
    area_candidates = numeric_mentions(AREA_RE, 'area_mentions_sqm', float, 10, 20000)
    room_candidates = numeric_mentions(ROOM_RE, 'bedroom_mentions',
                                       lambda value: int(value) if value.isascii()
                                       else ROOM_NUMERALS[value])
    district_candidates = [d for d in DISTRICTS if d in text]
    for district in district_candidates:
        start = find_in_source(district)
        if start is not None:
            item = evidence('district_mentions', district, start, start + len(district))
            evidence_items.append(item)
    community_candidates = [n for n in (known_community_names or [])
                            if n and any(n in value for _, value in sources)]
    community_candidates.sort(key=len, reverse=True)
    for community in dict.fromkeys(community_candidates):
        start = find_in_source(community)
        if start is not None:
            item = evidence('community_mentions', community, start, start + len(community))
            evidence_items.append(item)
    return {
        'method': 'rule_based_hints_not_verified',
        'price_mentions_wan': price_candidates,
        'area_mentions_sqm': area_candidates,
        'bedroom_mentions': room_candidates,
        'district_mentions': district_candidates,
        'community_mentions': list(dict.fromkeys(community_candidates)),
        'confidence_status': 'not_calibrated',
        'evidence': evidence_items,
        'warning': '口播/字幕可能混有原价、现价、他套房及广告信息；不得自动当作正式挂牌价。'
    }
