"""Rule-based comparable listing evidence; never an AI or transaction valuation."""
from decimal import Decimal, ROUND_HALF_UP
from app.db import session

MIN_RELIABLE_SAMPLE_COUNT = 5
_HISTORY_LIMIT = 12
_CENTS = Decimal('0.01')


def _empty_result(community_name, area_sqm, bedrooms, area_tolerance_pct,
                  asking_price_wan, community=None):
    return {
        'status': 'insufficient_data',
        'community': community or {
            'name': community_name, 'verified': False, 'district': None,
        },
        'query': {
            'area_sqm': area_sqm, 'bedrooms': bedrooms,
            'area_tolerance_pct': area_tolerance_pct,
            'asking_price_wan': asking_price_wan,
        },
        'sample_count': 0,
        'minimum_sample_count_for_reference_band': MIN_RELIABLE_SAMPLE_COUNT,
        'price_basis': 'platform_listed_asking_price',
        'unit_price_distribution_wan_per_sqm': None,
        'comparable_asking_price_band_wan': None,
        'asking_price_position': None,
        'comparables': [],
        'limitations': [
            '没有足够的同小区相似面积已审核挂牌记录。',
            '本接口不含真实成交价；视频口播或经纪人声称的报价不会作为样本。',
        ],
    }


def _money(value):
    if value is None:
        return None
    return Decimal(value).quantize(_CENTS, rounding=ROUND_HALF_UP)


def analyze_listings(community_name, area_sqm, bedrooms=None,
                     area_tolerance_pct=Decimal('10'),
                     asking_price_wan=None, limit=30):
    """Compare a subject with same-community Beike/Anjuke asking listings.

    Area deviation is relative to the requested property area. Only listings not
    explicitly withdrawn/sold are eligible; unknown status remains visible.
    Agent/video claim rows in price_history are excluded from all calculations.
    """
    with session() as conn:
        community = conn.execute('''SELECT c.id,c.name,c.district,c.verified
            FROM communities c
            WHERE c.city='宁波' AND (
                c.name=%s OR EXISTS (
                    SELECT 1 FROM community_aliases a
                    WHERE a.city=c.city AND a.community_id=c.id AND a.alias=%s
                )
            )
            ORDER BY (c.name=%s) DESC,c.verified DESC,c.name LIMIT 1''',
            (community_name, community_name, community_name)).fetchone()
        if community is None:
            return _empty_result(community_name, area_sqm, bedrooms,
                                 area_tolerance_pct, asking_price_wan)

        conditions = [
            'p.community_id=%s',
            "l.source IN ('beike','anjuke')",
            "l.status NOT IN ('withdrawn','sold')",
            "l.last_observed_at >= now() - interval '90 days'",
            'l.last_observed_at <= now()',
            'ABS(p.area_sqm-%s)/%s <= %s/100',
        ]
        values = [community['id'], area_sqm, area_sqm, area_tolerance_pct]
        if bedrooms is not None:
            conditions.append('p.bedrooms=%s')
            values.append(bedrooms)
        where = ' AND '.join(conditions)
        summary = conn.execute('''SELECT count(*)::int AS sample_count,
            percentile_disc(0.25) WITHIN GROUP
                (ORDER BY l.asking_price_wan/NULLIF(p.area_sqm,0)) AS p25,
            percentile_disc(0.50) WITHIN GROUP
                (ORDER BY l.asking_price_wan/NULLIF(p.area_sqm,0)) AS median,
            percentile_disc(0.75) WITHIN GROUP
                (ORDER BY l.asking_price_wan/NULLIF(p.area_sqm,0)) AS p75,
            min(l.asking_price_wan/NULLIF(p.area_sqm,0)) AS minimum,
            max(l.asking_price_wan/NULLIF(p.area_sqm,0)) AS maximum
            FROM source_listings l
            JOIN properties p ON p.id=l.property_id WHERE ''' + where,
            values).fetchone()

        selected = conn.execute('''SELECT l.id AS listing_id,l.source,
            l.source_listing_id,l.title,l.listing_url,l.asking_price_wan,l.status,
            l.last_observed_at,p.area_sqm,p.bedrooms,p.floor_text,p.decoration,
            l.asking_price_wan/NULLIF(p.area_sqm,0) AS asking_price_per_sqm_wan,
            ABS(p.area_sqm-%s)/%s*100 AS area_deviation_pct
            FROM source_listings l
            JOIN properties p ON p.id=l.property_id WHERE ''' + where + '''
            ORDER BY ABS(p.area_sqm-%s),l.last_observed_at DESC,l.source,l.source_listing_id
            LIMIT %s''',
            (area_sqm, area_sqm, *values, area_sqm, limit)).fetchall()

        history_by_listing = {row['listing_id']: [] for row in selected}
        if history_by_listing:
            history = conn.execute('''SELECT listing_id,price_wan,observed_at,evidence_url
                FROM (
                    SELECT listing_id,price_wan,observed_at,evidence_url,
                        row_number() OVER (
                            PARTITION BY listing_id ORDER BY observed_at DESC,id DESC
                        ) AS history_rank
                    FROM price_history
                    WHERE listing_id=ANY(%s) AND quote_type='platform_listed'
                ) recent
                WHERE history_rank<=%s
                ORDER BY listing_id,observed_at''',
                (list(history_by_listing), _HISTORY_LIMIT)).fetchall()
            for point in history:
                history_by_listing[point['listing_id']].append({
                    'price_wan': point['price_wan'],
                    'observed_at': point['observed_at'],
                    'evidence_url': point['evidence_url'],
                    'price_type': 'platform_listed_asking_price',
                })

    sample_count = summary['sample_count']
    result = {
        'status': 'sufficient_listing_evidence' if sample_count >= MIN_RELIABLE_SAMPLE_COUNT
                  else 'insufficient_data',
        'community': {
            'name': community['name'], 'verified': community['verified'],
            'district': community['district'],
        },
        'query': {
            'area_sqm': area_sqm, 'bedrooms': bedrooms,
            'area_tolerance_pct': area_tolerance_pct,
            'asking_price_wan': asking_price_wan,
        },
        'sample_count': sample_count,
        'minimum_sample_count_for_reference_band': MIN_RELIABLE_SAMPLE_COUNT,
        'price_basis': 'platform_listed_asking_price',
        'unit_price_distribution_wan_per_sqm': None,
        'comparable_asking_price_band_wan': None,
        'asking_price_position': None,
        'comparables': [],
        'limitations': [
            '挂牌价分布只反映挂牌报价，不是成交价或收益保证。',
            '视频口播与经纪人声称报价不会写入或参与挂牌价样本。',
            '挂牌状态为 unknown 的记录未确认仍在售，页面需显示该状态。',
            '同一套房跨来源去重身份未经确认；样本数按来源挂牌记录计数。',
        ],
    }
    if sample_count:
        result['unit_price_distribution_wan_per_sqm'] = {
            'minimum': summary['minimum'], 'p25': summary['p25'],
            'median': summary['median'], 'p75': summary['p75'],
            'maximum': summary['maximum'],
            'method': 'nearest_rank_percentiles_over_all_eligible_listings',
        }
    if sample_count >= MIN_RELIABLE_SAMPLE_COUNT:
        result['comparable_asking_price_band_wan'] = {
            'low': _money(summary['p25'] * area_sqm),
            'high': _money(summary['p75'] * area_sqm),
            'basis': 'same_community_comparable_listing_interquartile_band',
            'is_transaction_estimate': False,
        }
        if asking_price_wan is not None:
            asking_unit = asking_price_wan / area_sqm
            median_unit = summary['median']
            result['asking_price_position'] = {
                'asking_price_per_sqm_wan': asking_unit,
                'premium_to_comparable_median_pct': _money(
                    (asking_unit - median_unit) / median_unit * Decimal('100')
                ),
                'basis': 'asking_price_against_comparable_listing_median',
            }

    for row in selected:
        item = dict(row)
        item['price_type'] = 'platform_listed_asking_price'
        item['price_history'] = history_by_listing.get(row['listing_id'], [])
        points = item['price_history']
        if len(points) >= 2:
            first, latest = points[0], points[-1]
            item['retained_history_change'] = {
                'from_price_wan': first['price_wan'],
                'to_price_wan': latest['price_wan'],
                'change_wan': latest['price_wan'] - first['price_wan'],
                'from_observed_at': first['observed_at'],
                'to_observed_at': latest['observed_at'],
                'evidence_url': latest['evidence_url'],
                'note': '变化仅覆盖返回的最近挂牌价历史记录。',
            }
        else:
            item['retained_history_change'] = None
        result['comparables'].append(item)
    return result
