"""Offline parser for public-page *samples*. Never executes HTML or makes network calls.

This is intentionally a conservative generic baseline, not a verified site-specific extractor.
Both sites change layouts; real snapshots and human review are required before approval.
"""
from __future__ import annotations

import ast
from contextvars import ContextVar
import hashlib
from io import StringIO
import re
from app.collectors.text_normalization import normalize_text_for_comparison
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from app.collectors.url_policy import CollectionError

PARSER_VERSION = 'generic-labelled-v0.2.167'
INLINE_CSS_PARSE_CACHE_LIMIT = 1024
MAX_VISIBLE_TEXT_CHARS = 35_000
_INLINE_CSS_PARSE_CACHE: ContextVar[
    dict[str, dict[str, str]] | None
] = ContextVar('inline_css_parse_cache', default=None)
_INLINE_CSS_CACHED_PROPERTIES = frozenset((
    'display', 'opacity', 'visibility', 'content-visibility', 'clip', 'clip-path',
    'mask', 'mask-image', '-webkit-mask', '-webkit-mask-image'))
NUMERIC_TEXT_PATTERN = r'(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?'
NUMERIC_RANGE_SEPARATOR = r'[-−－–—~～〜至到]'
NON_LISTING_PRICE_CONTEXTS = ('成交', '交易', '历史', '原始', '预估', '网签', '合同', '签约', '口播',
                              '评估')
NON_LISTING_PRICE_CONTEXT_PATTERN = re.compile(
    '(?:' + '|'.join(r'\s*'.join(map(re.escape, context))
                      for context in NON_LISTING_PRICE_CONTEXTS) + ')'
    r'\s*(?:的|中(?:\s*的)?|里(?:\s*的)?)\s*$'
)
DISTRICTS = ('鄞州', '海曙', '江北', '镇海', '北仑', '奉化', '慈溪', '余姚', '宁海', '象山')
TEXT_FIELD_STOP_CHARS = r'\s,，;；|｜/：:。！？、'
BLOCK_TEXT_TAGS = {
    'address', 'article', 'blockquote', 'br', 'center', 'dd', 'details', 'div', 'dl', 'dt',
    'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3',
    'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main', 'nav', 'ol', 'p', 'pre',
    'section', 'summary', 'table', 'td', 'th', 'tr', 'ul',
}
BLOCK_TEXT_DISPLAY_VALUES = {
    'block', 'run-in', 'flow', 'flow-root', 'table', 'flex', 'grid', 'list-item', 'table-row',
    'table-cell', 'table-column', 'table-column-group', 'table-header-group',
    'table-footer-group', 'table-row-group', 'table-caption', 'block flow',
    'block flow-root', 'block flex', 'block grid', 'block table', 'block ruby',
    'block flow list-item', 'block flow-root list-item',
}
INLINE_TEXT_DISPLAY_VALUES = {
    'inline', 'inline-block', 'inline-table', 'inline-flex', 'inline-grid',
    'contents', 'ruby', 'inline flow', 'inline flow-root',
    'inline flex', 'inline grid', 'inline table', 'inline ruby', 'inline flow list-item',
    'initial', 'unset',
}
INLINE_DISPLAY_VALUES = {
    'block', 'inline', 'run-in', 'flow', 'flow-root', 'table', 'flex', 'grid',
    'ruby', 'list-item', 'contents', 'inline-block', 'inline-table',
    'inline-flex', 'inline-grid', 'table-row', 'table-cell', 'table-column',
    'table-column-group', 'table-header-group', 'table-footer-group',
    'table-row-group', 'table-caption', 'block flow', 'block flow-root',
    'block flex', 'block grid', 'block table', 'block ruby', 'inline flow',
    'inline flow-root', 'inline flex', 'inline grid', 'inline table',
    'inline ruby', 'block flow-root list-item', 'inline flow list-item',
    'initial', 'inherit', 'unset',
}


def _first_unique(pattern: str, text: str, flags: int = re.IGNORECASE):
    unique = {}
    for match in re.finditer(pattern, text, flags):
        value = match.group(1)
        if not isinstance(value, str) or not value.strip():
            continue
        value = value.strip()
        unique.setdefault(normalize_text_for_comparison(value), value)
        if len(unique) > 1:
            break
    unique = list(unique.values())
    return (unique[0] if len(unique) == 1 else None), unique


def _unique_text_values(values: Iterable[str]) -> list[str]:
    unique = {}
    for value in values:
        if isinstance(value, str) and value.strip():
            text = value.strip()
            unique.setdefault(normalize_text_for_comparison(text), text)
            if len(unique) > 1:
                break
    return list(unique.values())


def _first_unique_numeric(pattern: str, text: str, flags: int = re.IGNORECASE):
    unique = {}
    for match_result in re.finditer(pattern, text, flags):
        match = match_result.group(1).strip()
        if not re.fullmatch(NUMERIC_TEXT_PATTERN, match):
            key = ('invalid', match)
        else:
            try:
                key = Decimal(match.replace(',', ''))
            except InvalidOperation:
                key = ('invalid', match)
        unique.setdefault(key, match)
        if len(unique) > 1:
            break
    if len(unique) != 1:
        return None, list(unique)
    key, value = next(iter(unique.items()))
    return (None if isinstance(key, tuple) else value), list(unique)


def _scan_field_evidence(pattern: str, text: str, *, numeric: bool = False,
                         flags: int = re.IGNORECASE, exclude_match=None,
                         mention_metadata=None):
    unique = {}
    mentions = []
    mention_count = 0
    for match in re.finditer(pattern, text, flags):
        if exclude_match is not None and exclude_match(match):
            continue
        raw_value = match.group(1).strip()
        mention_count += 1
        if numeric:
            if not re.fullmatch(NUMERIC_TEXT_PATTERN, raw_value):
                key = ('invalid', raw_value)
            else:
                try:
                    key = Decimal(raw_value.replace(',', ''))
                except InvalidOperation:
                    key = ('invalid', raw_value)
        elif raw_value:
            key = normalize_text_for_comparison(raw_value)
        else:
            key = None
        if key is not None and (key in unique or len(unique) < 2):
            unique.setdefault(key, raw_value)
        if len(mentions) < 20:
            start, end = match.span()
            while start < end and text[start].isspace():
                start += 1
            while start < end and text[end - 1].isspace():
                end -= 1
            mention = {
                'candidate_value': raw_value,
                'source': 'visible_listing_text',
                'quote': text[start:end],
                'start_char': start,
                'end_char': end,
            }
            if mention_metadata is not None:
                mention.update(mention_metadata(match))
            mentions.append(mention)
    unique_values = list(unique.values())
    if numeric:
        if len(unique) != 1:
            value = None
        else:
            key, raw_value = next(iter(unique.items()))
            value = None if isinstance(key, tuple) else raw_value
    else:
        value = unique_values[0] if len(unique_values) == 1 else None
    evidence = {
        'mentions': mentions,
        'mention_count': mention_count,
        'mentions_truncated': mention_count > len(mentions),
    }
    return value, unique_values, evidence


def _negative_label_prefixes(prefixes: tuple[str, ...]) -> str:
    """Reject labels directly preceded by a qualifier, with normalized whitespace."""
    return ''.join(
        f'(?<!{re.escape(prefix + separator)})'
        for prefix in prefixes for separator in ('', ' ', ':', '：', ': ', '： ')
    )


def _number_str(val: str | None, lo: float, hi: float, *, minimum_exclusive: bool = False):
    if not val:
        return None
    val = val.strip()
    if not re.fullmatch(NUMERIC_TEXT_PATTERN, val):
        return None
    try:
        n = Decimal(val.replace(',', ''))
    except InvalidOperation:
        return None
    lower_bound = Decimal(str(lo))
    if (n < lower_bound or minimum_exclusive and n == lower_bound
            or n > Decimal(str(hi))):
        return None
    parsed = float(n)
    return None if n != 0 and parsed == 0 else parsed


def _requires_subcent_correction(value: str) -> bool:
    number = Decimal(value.replace(',', ''))
    exponent = number.as_tuple().exponent
    if exponent >= -2:
        return False
    trailing_places = -2 - exponent
    return any(number.as_tuple().digits[-trailing_places:])


def _decode_css_escapes(value: str) -> str:
    def decode(match):
        hexadecimal, escaped = match.groups()
        if escaped is not None:
            return escaped
        codepoint = int(hexadecimal, 16)
        if codepoint == 0 or codepoint > 0x10FFFF or 0xD800 <= codepoint <= 0xDFFF:
            return '\ufffd'
        return chr(codepoint)

    return re.sub(
        r'\\([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?|\\([^\r\n\f])',
        decode, value)


def _contains_css_var(value: str) -> bool:
    return re.search(r'\bvar\(', _decode_css_escapes(value)) is not None


def _contains_escaped_ascii_digit(value: str) -> bool:
    for match in re.finditer(r'\\([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?', value):
        if 0x30 <= int(match.group(1), 16) <= 0x39:
            return True
    return False


def _contains_escaped_css_math_syntax(value: str) -> bool:
    for match in re.finditer(
            r'\\([0-9a-fA-F]{1,6})(?:\r\n|[ \t\r\n\f])?|\\([^\r\n\f])', value):
        hexadecimal, escaped = match.groups()
        character = escaped if escaped is not None else chr(int(hexadecimal, 16))
        if character in '()+-*/%.':
            return True
    return False


def _split_css_important(value: str) -> tuple[str, str | None]:
    depth = 0
    quote = None
    index = 0
    while index < len(value):
        char = value[index]
        if char == '\\':
            index += 1
            if index < len(value) and value[index] in '0123456789abcdefABCDEF':
                digits = 0
                while (index < len(value) and digits < 6
                       and value[index] in '0123456789abcdefABCDEF'):
                    index += 1
                    digits += 1
                if index < len(value) and value[index] in ' \t\r\n\f':
                    index += 1
                continue
            index += 1
            continue
        if quote is not None:
            if char == quote:
                quote = None
        elif char in ('"', "'"):
            quote = char
        elif char in '([{':
            depth += 1
        elif char in ')]}':
            depth = max(0, depth - 1)
        elif char == '!' and depth == 0:
            return value[:index], value[index + 1:]
        index += 1
    return value, None


def _valid_inline_css_value(property_name: str, value: str) -> bool:
    css_wide_keywords = {'inherit', 'initial', 'revert', 'revert-layer', 'unset'}
    if property_name == 'display':
        return (_contains_css_var(value)
                or value in (css_wide_keywords | INLINE_DISPLAY_VALUES
                             | BLOCK_TEXT_DISPLAY_VALUES | {'none'}))
    if property_name == 'opacity':
        if value in css_wide_keywords or _contains_css_var(value):
            return True
        number = r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
        if re.fullmatch(rf'{number}%?', value):
            return True
        match = re.fullmatch(r'(calc|min|max|clamp)\((.*)\)', value)
        if match:
            expression = match.group(2) if match.group(1) == 'calc' else value
            return _css_numeric_math(expression.strip()) is not None
        return False
    if property_name == 'visibility':
        return (_contains_css_var(value)
                or value in css_wide_keywords | {'visible', 'hidden', 'collapse'})
    if property_name == 'content-visibility':
        return (_contains_css_var(value)
                or value in css_wide_keywords | {'visible', 'hidden', 'auto'})
    return True


def _iter_css_declarations(style: str) -> Iterable[str]:
    for match in re.finditer(r'[^;]+', style):
        yield match.group()


def _scan_inline_css_values(style: str, property_names: Iterable[str]) -> dict[str, str]:
    property_names = set(property_names)
    style = re.sub(r'/\*.*?(?:\*/|$)', '', style, flags=re.DOTALL)
    selected_values = {}
    selected_important = {}
    for declaration in _iter_css_declarations(style):
        name, separator, value = declaration.partition(':')
        if not separator:
            continue
        property_name = _decode_css_escapes(name.strip()).lower()
        if property_name not in property_names:
            continue
        value, priority = _split_css_important(value)
        important = (priority is not None
                     and _decode_css_escapes(priority.strip()).lower() == 'important')
        if priority is not None and not important:
            continue
        if (property_name == 'opacity' and not _contains_css_var(value)
                and _contains_escaped_css_math_syntax(value)):
            continue
        if (property_name == 'opacity' and not _contains_css_var(value)
                and _contains_escaped_ascii_digit(value)):
            continue
        value = re.sub(
            r'[ \t\r\n\f]+', ' ',
            _decode_css_escapes(value.strip(' \t\r\n\f')).lower())
        if not _valid_inline_css_value(property_name, value):
            continue
        if (property_name not in selected_values or important
                or not selected_important.get(property_name, False)):
            selected_values[property_name] = value
            selected_important[property_name] = important
    return selected_values


def _inline_css_values(style: str, property_names: Iterable[str]) -> dict[str, str]:
    property_names = frozenset(property_names)
    cache = _INLINE_CSS_PARSE_CACHE.get()
    if cache is None or INLINE_CSS_PARSE_CACHE_LIMIT <= 0:
        return _scan_inline_css_values(style, property_names)
    if style in cache:
        values = cache[style]
    else:
        values = _scan_inline_css_values(style, _INLINE_CSS_CACHED_PROPERTIES)
        if len(cache) >= INLINE_CSS_PARSE_CACHE_LIMIT:
            cache.pop(next(iter(cache)))
        cache[style] = values
    return {name: values[name] for name in property_names if name in values}


def _inline_css_value(style: str, property_name: str) -> str | None:
    return _inline_css_values(style, (property_name,)).get(property_name)


def _inline_display_none(style: str) -> bool:
    return _inline_css_value(style, 'display') == 'none'


def _inline_display_overrides_hidden(style: str) -> bool:
    value = _inline_css_value(style, 'display')
    return value in INLINE_DISPLAY_VALUES or (value is not None and _contains_css_var(value))


def _remove_non_visible_tags(root: Tag | BeautifulSoup) -> None:
    omitted_tags = {'script', 'style', 'template', 'nav', 'menu', 'aside', 'footer',
                    'noscript', 'svg', 'iframe', 'object', 'embed', 'canvas', 'form',
                    'button', 'select', 'textarea'}
    pending = [root]
    while pending:
        parent = pending.pop()
        for child in reversed(parent.contents):
            if not isinstance(child, Tag):
                continue
            style_value = (_inline_css_values(child.get('style', ''), ('display',))
                           if child.has_attr('style') else {}).get('display')
            remove = child.name in omitted_tags
            if child.name == 'dialog' and not child.has_attr('open'):
                remove = True
            if child.has_attr('hidden'):
                hidden_value = str(child.get('hidden', '')).strip().lower()
                display_overrides_hidden = (
                    style_value in INLINE_DISPLAY_VALUES
                    or style_value is not None and _contains_css_var(style_value))
                if hidden_value == 'until-found' or not display_overrides_hidden:
                    remove = True
            if style_value == 'none':
                remove = True
            if remove:
                child.decompose()
            else:
                pending.append(child)


def _has_unresolved_inline_visibility(node: Tag | BeautifulSoup,
                                      textful_nodes: set[int] | None = None) -> bool:
    pending = [(node, False)]
    textful = textful_nodes if textful_nodes is not None else set()
    unresolved = False
    while pending:
        current, closing = pending.pop()
        if not isinstance(current, Tag):
            continue
        if closing:
            has_text = any(
                (isinstance(child, NavigableString) and not isinstance(child, Comment)
                 and bool(str(child).strip()))
                or (isinstance(child, Tag) and id(child) in textful)
                for child in current.contents
            )
            if not has_text:
                continue
            textful.add(id(current))
            if current is node or not current.has_attr('style'):
                continue
            style = current.get('style', '')
            if _has_escaped_opacity_math_syntax(style):
                if textful_nodes is None:
                    return True
                unresolved = True
                continue
            values = _inline_css_values(style, (
                'display', 'opacity', 'visibility', 'content-visibility', 'clip',
                'clip-path', 'mask', 'mask-image', '-webkit-mask', '-webkit-mask-image'))
            if any((value := values.get(property_name)) is not None
                   and (property_name in ('clip', 'clip-path', 'mask', 'mask-image',
                                          '-webkit-mask', '-webkit-mask-image')
                        or _contains_css_var(value)
                        or (property_name == 'content-visibility' and value == 'auto'))
                   for property_name in ('display', 'opacity', 'visibility',
                                         'content-visibility', 'clip', 'clip-path',
                                         'mask', 'mask-image', '-webkit-mask',
                                         '-webkit-mask-image')):
                if textful_nodes is None:
                    return True
                unresolved = True
            continue
        pending.append((current, True))
        pending.extend((child, False) for child in reversed(current.contents)
                       if isinstance(child, Tag))
    return unresolved


def _css_without_comments_or_strings(css: str) -> str:
    visible = StringIO()
    index = 0
    copy_start = 0
    quote = None
    while index < len(css):
        char = css[index]
        if char == '\\':
            index += 1
            if index < len(css) and css[index] in '0123456789abcdefABCDEF':
                digits = 0
                while (index < len(css) and digits < 6
                       and css[index] in '0123456789abcdefABCDEF'):
                    index += 1
                    digits += 1
                if index < len(css) and css[index] in ' \t\r\n\f':
                    if css[index] == '\r' and index + 1 < len(css) and css[index + 1] == '\n':
                        index += 1
                    index += 1
            elif index < len(css):
                index += 1
            continue
        if quote is not None:
            if char == quote:
                quote = None
                visible.write(' ')
            index += 1
            if quote is None:
                copy_start = index
            continue
        if css.startswith('/*', index):
            end = css.find('*/', index + 2)
            visible.write(css[copy_start:index])
            visible.write(' ')
            index = len(css) if end < 0 else end + 2
            copy_start = index
            continue
        if char in ('"', "'"):
            quote = char
            visible.write(css[copy_start:index])
            visible.write(' ')
            index += 1
            copy_start = index
            continue
        index += 1
    if quote is None:
        visible.write(css[copy_start:])
    return visible.getvalue()


def _css_rule_segments(css: str) -> Iterable[str]:
    start = 0
    index = 0
    parentheses = 0
    brackets = 0
    custom_property_blocks = 0
    while index < len(css):
        char = css[index]
        if char == '\\':
            index += 1
            if index < len(css) and css[index] in '0123456789abcdefABCDEF':
                digits = 0
                while (index < len(css) and digits < 6
                       and css[index] in '0123456789abcdefABCDEF'):
                    index += 1
                    digits += 1
                if index < len(css) and css[index] in ' \t\r\n\f':
                    if css[index] == '\r' and index + 1 < len(css) and css[index + 1] == '\n':
                        index += 1
                    index += 1
            elif index < len(css):
                index += 1
            continue
        if char == '(':
            parentheses += 1
        elif char == ')':
            parentheses = max(0, parentheses - 1)
        elif char == '[':
            brackets += 1
        elif char == ']':
            brackets = max(0, brackets - 1)
        elif parentheses == 0 and brackets == 0:
            if char == '{':
                if custom_property_blocks:
                    custom_property_blocks += 1
                else:
                    custom_property = re.match(
                        r'\s*--[^\s:]+\s*:', _decode_css_escapes(css[start:index]))
                    if custom_property:
                        custom_property_blocks = 1
                    else:
                        yield css[start:index]
                        start = index + 1
            elif char == '}' and custom_property_blocks:
                custom_property_blocks -= 1
            elif char == ';' and custom_property_blocks:
                pass
            elif char in ';{}':
                yield css[start:index]
                start = index + 1
        index += 1
    yield css[start:]


def _has_unresolved_stylesheet_visibility(soup: BeautifulSoup) -> bool:
    visibility_properties = (
        r'(?:display|opacity|visibility|content-visibility|clip(?:-path)?'
        r'|(?:-webkit-)?mask(?:-image)?)')
    inert_subtree_tags = set()
    for tag in soup.descendants:
        if not isinstance(tag, Tag):
            continue
        parent = tag.parent
        inert = (tag.name in ('template', 'noscript')
                 or isinstance(parent, Tag) and id(parent) in inert_subtree_tags)
        if inert:
            inert_subtree_tags.add(id(tag))
            continue
        if not inert and tag.name == 'style':
            css = _css_without_comments_or_strings(tag.get_text())
            for segment in _css_rule_segments(css):
                segment = _decode_css_escapes(segment).strip()
                if (re.match(rf'{visibility_properties}\s*:', segment, re.IGNORECASE)
                        or re.match(r'@import\b', segment, re.IGNORECASE)):
                    return True
        elif not inert and tag.name == 'link' and any(
                str(relation).lower() == 'stylesheet' for relation in (tag.get('rel') or [])):
            return True
    return False


def _has_escaped_opacity_math_syntax(style: str) -> bool:
    style = re.sub(r'/\*.*?(?:\*/|$)', '', style, flags=re.DOTALL)
    for declaration in _iter_css_declarations(style):
        name, separator, value = declaration.partition(':')
        if not separator or _decode_css_escapes(name.strip()).lower() != 'opacity':
            continue
        value, _ = _split_css_important(value)
        if _contains_escaped_css_math_syntax(value):
            return True
    return False


def _css_numeric_math(expression: str) -> Decimal | None:
    if len(expression) > 256:
        return None
    number = r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
    expression = re.sub(
        rf'(?<![\w.])({number})%', r'(\1/100)', expression)
    try:
        tree = ast.parse(expression, mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 128:
            return None
    except (RecursionError, SyntaxError, ValueError):
        return None

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            raw = ast.get_source_segment(expression, node)
            if raw is None or not re.fullmatch(number, raw):
                return None
            try:
                return Decimal(raw)
            except InvalidOperation:
                return None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = evaluate(node.operand)
            if value is None:
                return None
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub,
                                                                  ast.Mult, ast.Div)):
            left = evaluate(node.left)
            right = evaluate(node.right)
            if left is None or right is None:
                return None
            try:
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                return left / right
            except (ArithmeticError, InvalidOperation):
                return None
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and not node.keywords):
            name = node.func.id
            if name not in ('min', 'max', 'clamp'):
                return None
            values = [evaluate(argument) for argument in node.args]
            if any(value is None for value in values):
                return None
            if name == 'clamp' and len(values) == 3:
                return max(values[0], min(values[1], values[2]))
            if name in ('min', 'max') and values:
                return min(values) if name == 'min' else max(values)
        return None

    return evaluate(tree)


def _inline_opacity_zero(style: str) -> bool:
    return _opacity_value_is_zero(_inline_css_value(style, 'opacity'))


def _opacity_value_is_zero(value: str | None) -> bool:
    if value is None:
        return False
    function_match = re.match(r'(calc|min|max|clamp)\(', value)
    if function_match and value.endswith(')'):
        name = function_match.group(1)
        expression = value[5:-1] if name == 'calc' else value
        calculated = _css_numeric_math(expression.strip())
        return calculated is not None and calculated <= 0
    if value.endswith('%'):
        value = value[:-1].strip()
    if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', value):
        return False
    try:
        return Decimal(value) <= 0
    except InvalidOperation:
        return False


def _inline_content_visibility_hidden(style: str) -> bool:
    return _inline_css_value(style, 'content-visibility') == 'hidden'


def _is_block_text_tag(tag: Tag) -> bool:
    current = tag
    while isinstance(current, Tag):
        display = _inline_css_value(current.get('style', ''), 'display')
        if display == 'inherit':
            current = current.parent
            continue
        if display == 'run-in':
            return not _run_in_sequence_is_inlinified(current)
        if display in BLOCK_TEXT_DISPLAY_VALUES:
            return True
        if display in INLINE_TEXT_DISPLAY_VALUES:
            return False
        return current.name in BLOCK_TEXT_TAGS
    return tag.name in BLOCK_TEXT_TAGS


def _run_in_target_is_block(tag: Tag) -> bool:
    display = _inline_css_value(tag.get('style', ''), 'display')
    return _display_value_is_block(tag, display)


def _display_value_is_block(tag: Tag, display: str | None) -> bool:
    if display in ('block', 'flow', 'block flow', 'block flow list-item'):
        return True
    if (display in BLOCK_TEXT_DISPLAY_VALUES or display in INLINE_TEXT_DISPLAY_VALUES
            or display in INLINE_DISPLAY_VALUES):
        return False
    return tag.name in BLOCK_TEXT_TAGS


def _run_in_sequence_is_inlinified(tag: Tag) -> bool:
    for sibling in tag.next_siblings:
        if isinstance(sibling, Comment):
            continue
        if isinstance(sibling, NavigableString):
            if str(sibling).strip():
                return False
            continue
        if not isinstance(sibling, Tag):
            continue
        display = _inline_css_value(sibling.get('style', ''), 'display')
        if display == 'run-in':
            continue
        return _run_in_target_is_block(sibling)
    return False


def _run_in_has_inline_predecessor(tag: Tag) -> bool:
    for sibling in tag.previous_siblings:
        if isinstance(sibling, Comment):
            continue
        if isinstance(sibling, NavigableString):
            if str(sibling).strip():
                return True
            continue
        if not isinstance(sibling, Tag):
            continue
        display = _inline_css_value(sibling.get('style', ''), 'display')
        if display == 'run-in' and _run_in_sequence_is_inlinified(sibling):
            continue
        return not _block_text_state(sibling, False)
    return False


def _is_inlinified_run_in_prefix(tag: Tag) -> bool:
    found = False
    for sibling in tag.previous_siblings:
        if isinstance(sibling, Comment):
            continue
        if isinstance(sibling, NavigableString):
            if str(sibling).strip():
                return found
            continue
        if not isinstance(sibling, Tag):
            continue
        if (_inline_css_value(sibling.get('style', ''), 'display') == 'run-in'
                and _run_in_sequence_is_inlinified(sibling)):
            found = True
            continue
        return found
    return found


def _run_in_sibling_layout(parent: Tag | BeautifulSoup):
    children = parent.contents
    displays = {}
    has_run_in = False
    for child in children:
        if isinstance(child, Tag) and child.has_attr('style'):
            display = _inline_css_value(child.get('style', ''), 'display')
            displays[id(child)] = display
            has_run_in = has_run_in or display == 'run-in'
    if not has_run_in:
        return {}, {}
    for child in children:
        if isinstance(child, Tag) and id(child) not in displays:
            displays[id(child)] = _inline_css_value(child.get('style', ''), 'display')

    significant = [child for child in children
                   if not isinstance(child, Comment)
                   and (isinstance(child, Tag)
                        or isinstance(child, NavigableString) and str(child).strip())]
    run_in_states = {}
    index = 0
    while index < len(significant):
        child = significant[index]
        if not isinstance(child, Tag) or displays[id(child)] != 'run-in':
            index += 1
            continue
        end = index
        while (end + 1 < len(significant)
               and isinstance(significant[end + 1], Tag)
               and displays[id(significant[end + 1])] == 'run-in'):
            end += 1
        following = significant[end + 1] if end + 1 < len(significant) else None
        sequence_inlinified = (
            isinstance(following, Tag)
            and displays[id(following)] != 'run-in'
            and _display_value_is_block(following, displays[id(following)]))
        previous = significant[index - 1] if index else None
        if isinstance(previous, NavigableString):
            has_inline_predecessor = True
        elif isinstance(previous, Tag):
            has_inline_predecessor = not _block_text_state(previous, False)
        else:
            has_inline_predecessor = False
        for run_in in significant[index:end + 1]:
            run_in_states[id(run_in)] = (sequence_inlinified, has_inline_predecessor)
        index = end + 1

    inlinified_prefixes = {}
    for index, child in enumerate(significant):
        if not isinstance(child, Tag) or not index:
            continue
        previous = significant[index - 1]
        inlinified_prefixes[id(child)] = (
            isinstance(previous, Tag)
            and displays.get(id(previous)) == 'run-in'
            and run_in_states.get(id(previous), (False, False))[0])
    return run_in_states, inlinified_prefixes


def _block_text_state(tag: Tag, inherited_block: bool,
                      run_in_states: dict[int, tuple[bool, bool]] | None = None) -> bool:
    display = _inline_css_value(tag.get('style', ''), 'display')
    if display == 'inherit':
        return inherited_block
    if display == 'run-in':
        if run_in_states is not None and id(tag) in run_in_states:
            sequence_inlinified, has_inline_predecessor = run_in_states[id(tag)]
            return not sequence_inlinified or has_inline_predecessor
        return (not _run_in_sequence_is_inlinified(tag)
                or _run_in_has_inline_predecessor(tag))
    if display in BLOCK_TEXT_DISPLAY_VALUES:
        return True
    if display in INLINE_TEXT_DISPLAY_VALUES:
        return False
    return tag.name in BLOCK_TEXT_TAGS


def _remove_inline_invisible_text(node: Tag | BeautifulSoup):
    pending = [(node, False, False, False, False, False, False)]
    while pending:
        (current, closing, inherited_hidden, ancestor_opacity_zero,
         ancestor_content_hidden, inside_collapsed_details, is_collapsed_details) = pending.pop()
        if closing:
            if is_collapsed_details and not inside_collapsed_details:
                summary = current.find('summary', recursive=False)
                if summary is None:
                    current.decompose()
                else:
                    summary_text = re.sub(r'\s+', ' ', _text_with_inline_boundaries(
                        summary, collapse_closed_details=True)).strip()
                    current.clear()
                    if summary_text:
                        current.append(summary_text)
            continue
        is_collapsed_details = current.name == 'details' and not current.has_attr('open')
        pending.append((current, True, inherited_hidden, ancestor_opacity_zero,
                        ancestor_content_hidden, inside_collapsed_details,
                        is_collapsed_details))
        for child in reversed(current.contents):
            if isinstance(child, NavigableString):
                if inherited_hidden or ancestor_opacity_zero or ancestor_content_hidden:
                    child.extract()
                continue
            if not isinstance(child, Tag):
                continue
            style = child.get('style', '')
            values = (_inline_css_values(
                style, ('visibility', 'opacity', 'content-visibility'))
                if child.has_attr('style') else {})
            value = values.get('visibility')
            if value in ('hidden', 'collapse'):
                hidden = True
            elif value in ('visible', 'initial'):
                hidden = False
            else:
                hidden = inherited_hidden
            opacity_zero = (ancestor_opacity_zero
                            or _opacity_value_is_zero(values.get('opacity')))
            content_hidden = (ancestor_content_hidden
                              or values.get('content-visibility') == 'hidden')
            pending.append((child, False, hidden, opacity_zero, content_hidden,
                            inside_collapsed_details or is_collapsed_details, False))


def _strip_text_parts(parts: list[str], start: int) -> None:
    while len(parts) > start and not parts[-1].strip():
        parts.pop()
    if len(parts) > start:
        parts[-1] = parts[-1].rstrip()
    leading = start
    while leading < len(parts) and not parts[leading].strip():
        leading += 1
    if leading > start:
        del parts[start:leading]
    if len(parts) > start:
        parts[start] = parts[start].lstrip()


def _normalize_text_prefix(text: str, limit: int) -> tuple[str, bool]:
    """Collapse whitespace and return only the visible prefix plus its truncation state."""
    if limit < 0:
        raise ValueError('text prefix limit must be non-negative')
    parts = []
    length = 0
    for match in re.finditer(r'(\s+)|(\S+)', text):
        whitespace_start, whitespace_end = match.span(1)
        if whitespace_start >= 0:
            if length == limit:
                return ''.join(parts), True
            parts.append(' ')
            length += 1
            continue
        start, end = match.span(2)
        remaining = limit - length
        if end - start > remaining:
            if remaining:
                parts.append(text[start:start + remaining])
            return ''.join(parts), True
        parts.append(text[start:end])
        length += end - start
    return ''.join(parts), False


def _text_with_inline_boundaries(node: Tag | BeautifulSoup,
                                 collapse_closed_details: bool = False) -> str:
    """Keep inline text contiguous, separating blocks and flattening closed details if asked."""
    parts = []

    inherited_block = _is_block_text_tag(node.parent) if isinstance(node, Tag) and isinstance(node.parent, Tag) else False
    pending = [(node, False, inherited_block, None)]
    run_in_layouts = {}
    while pending:
        current, closing, inherited_block, trim_start = pending.pop()
        if isinstance(current, Comment):
            continue
        if isinstance(current, NavigableString):
            if not closing:
                parts.append(str(current))
            continue
        if not isinstance(current, Tag):
            continue
        if closing:
            if inherited_block:
                parts.append('\n')
            if trim_start is not None:
                _strip_text_parts(parts, trim_start)
            continue
        collapsed_summary = None
        if (collapse_closed_details and current.name == 'details'
                and not current.has_attr('open')):
            collapsed_summary = current.find('summary', recursive=False)
            if collapsed_summary is None:
                continue
        parent = current.parent
        layout = run_in_layouts.get(id(parent)) if parent is not None else None
        if layout is None and parent is not None and len(parent.contents) > 1:
            layout = _run_in_sibling_layout(parent)
            run_in_layouts[id(parent)] = layout
        run_in_states, inlinified_prefixes = layout or (None, None)
        is_block = _block_text_state(current, inherited_block, run_in_states)
        is_inlinified_prefix = (
            inlinified_prefixes.get(id(current), False)
            if inlinified_prefixes is not None
            else _is_inlinified_run_in_prefix(current))
        if collapsed_summary is not None:
            pending.append((current, True, is_block, None))
            pending.append((collapsed_summary, False,
                            _is_block_text_tag(current), len(parts)))
            continue
        if is_block and not is_inlinified_prefix:
            parts.append('\n')
        pending.append((current, True, is_block, trim_start))
        pending.extend((child, False, is_block, None)
                       for child in reversed(current.contents))
    return ''.join(parts)


@dataclass(frozen=True)
class ParseResult:
    fields: dict
    warnings: list[str]
    sha256: str
    parser_version: str = PARSER_VERSION

    @property
    def ready_for_review(self) -> bool:
        required = ('source_listing_id', 'community_name', 'area_sqm', 'asking_price_wan')
        return all(self.fields.get(k) is not None for k in required) and not any(
            warning in ('multiple_area_mentions', 'multiple_price_mentions', 'visible_text_truncated')
            or warning in ('unresolved_inline_visibility', 'unresolved_stylesheet_visibility')
            or warning == 'non_exact_asking_price'
            or warning == 'non_exact_area_sqm'
            or warning.startswith('numeric_precision_requires_correction:')
            for warning in self.warnings
        )


def parse_generic_listing_html(source_url: str, html: str,
                               extract_source_id: Callable[[str], str | None]) -> ParseResult:
    """Parse a saved page into a *review candidate*, never into a confirmed listing.

    Prefers explicitly labelled attributes/visible text. Unknown fields remain null.
    Does NOT infer IDs from title, images, phone numbers or addresses.
    """
    cache_token = _INLINE_CSS_PARSE_CACHE.set({})
    try:
        return _parse_generic_listing_html(source_url, html, extract_source_id)
    finally:
        _INLINE_CSS_PARSE_CACHE.reset(cache_token)


def _parse_generic_listing_html(source_url: str, html: str,
                                extract_source_id: Callable[[str], str | None]) -> ParseResult:
    if not isinstance(html, str) or len(html) < 20:
        raise CollectionError('HTML sample must contain at least 20 characters and at most 1,000,000 UTF-8 bytes')
    if len(html) > 1_000_000:
        raise CollectionError('HTML sample must contain at least 20 characters and at most 1,000,000 UTF-8 bytes')
    try:
        html_bytes = html.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise CollectionError('HTML sample must be valid UTF-8 text') from exc
    if len(html_bytes) > 1_000_000:
        raise CollectionError('HTML sample must contain at least 20 characters and at most 1,000,000 UTF-8 bytes')
    if '\x00' in html:
        raise CollectionError('HTML sample must not contain a NUL character')
    soup = BeautifulSoup(html, 'html.parser')
    unresolved_stylesheet_visibility = _has_unresolved_stylesheet_visibility(soup)
    # Remove excluded and explicitly hidden subtrees in one walk of the document.
    _remove_non_visible_tags(soup)
    _remove_inline_invisible_text(soup)
    textful_node_ids = set()
    unresolved_inline_visibility = _has_unresolved_inline_visibility(soup, textful_node_ids)
    community_labels = r'(?:小区名称|所在小区|小区)'
    next_field_labels = (
        rf'(?:{community_labels}|建筑面积|建面|面积|挂牌总价|挂牌价|出售总价|总价|'
        r'所在区域|行政区|区域|户型|房型|总楼层|(?<!总)楼层|装修情况|装修状况|装修状态|装修)')
    community_next_field = rf'{next_field_labels}\s*[:：]'
    free_text_value_chars = r'[^,，、;；|｜。！？:：<>]'
    free_text_value_end = (
        rf'(?=[,，、;；|｜。！？<>]|/(?:{next_field_labels})\s*[:：]|'
        rf'{next_field_labels}\s*[:：]|$)')
    community_pattern = (rf'{community_labels}\s*[:：]\s*'
                         rf'([^{TEXT_FIELD_STOP_CHARS}\[\]<>]{{2,180}}?)'
                         rf'(?=[{TEXT_FIELD_STOP_CHARS}\[\]<>]|{community_next_field}|$)')
    non_listing_price_prefixes = (
        '折后', '优惠后', '优惠', '折扣后', '降价后', '参考', '估算', '成交', '交易',
        '历史', '原始', '预估', '网签', '合同', '签约', '口播', '口播：',
        '评估', '租金', '月租', '年租', '原')
    price_labels = r'(?:挂牌总价|挂牌价|挂牌售价|(?<!挂牌)售价|出售总价|(?<!挂牌)(?<!出售)总价)'
    price_number = r'[0-9,]+(?:\.[0-9]+)?'
    range_separator = NUMERIC_RANGE_SEPARATOR
    range_endpoint_start = r'(?:[0-9零〇一二两三四五六七八九十百千万]|$)'
    price_prefix = _negative_label_prefixes(non_listing_price_prefixes)
    price_per_area_suffix = (
        r'\s*(?:[（(]\s*)?元?\s*(?:[（(]\s*)?(?:[/／]|每)\s*'
        r'(?:㎡|m²|平米|平方米|平|平方)\s*(?:[）)])?'
    )
    price_per_period_suffix = (
        r'\s*(?:[（(]\s*)?元?\s*(?:[（(]\s*)?(?:[/／]|每)\s*'
        r'(?:年|月|日|天|周|小时|季度)\s*(?:[）)])?'
    )
    def is_linked_non_listing_price(match, candidate_text: str) -> bool:
        preceding_text = candidate_text[max(0, match.start() - 32):match.start()]
        return NON_LISTING_PRICE_CONTEXT_PATTERN.search(preceding_text) is not None

    def linked_non_listing_price(match):
        return is_linked_non_listing_price(match, text)

    non_exact_price_before_number_source = (
        r'(?:>=|<=|>|<|≥|≤|≧|≦|大约|约|大概|左右|上下|出头|附近|以上|以下|以内|不到|不足|'
        r'不超过|不高于|不低于|至少|至多|最低|最高|参考|估算|估计|预估|在|'
        r'封顶|起价|起售|起步价|起步|起始价)'
    )
    non_exact_price_suffix_source = (
        r'\s*元?\s*(?:[（(]\s*)?'
        r'(?:约|大约|大概|左右|上下|出头|附近|以上|以下|以内|不到|不足|'
        r'不超过|不高于|不低于|封顶|起价|起售房源|起售|起步价|起步|起始价|[+＋]|'
        r'起(?=$|[\s，,。；;：:）)]))'
        r'(?:\s*[）)])?'
    )
    non_exact_price_suffix = re.compile(non_exact_price_suffix_source)
    price_label_pattern = (
        price_prefix + price_labels + r'\s*[:：]?\s*'
        + r'(?:为\s*)?'
        + rf'(?:{non_exact_price_before_number_source}\s*[:：]?\s*)?'
        + r'(?:为\s*)?'
    )
    price_pattern = (price_label_pattern
                     + r'([0-9,]+(?:\.[0-9]+)?)\s*万'
                     + rf'(?:{non_exact_price_suffix_source})?'
                     + rf'(?!{price_per_area_suffix})'
                     + rf'(?!{price_per_period_suffix})'
                     rf'(?!\s*{range_separator}\s*{range_endpoint_start})')
    price_range_pattern = (
        price_label_pattern
        + rf'({price_number}\s*万?\s*{range_separator}\s*{price_number}\s*万)'
        + rf'(?:{non_exact_price_suffix_source})?')
    price_range_pattern += rf'(?!{price_per_area_suffix})'
    price_range_pattern += rf'(?!{price_per_period_suffix})'
    non_exact_price_before_number = re.compile(
        rf'{non_exact_price_before_number_source}\s*[:：]?\s*(?:为\s*)?$'
    )

    def has_non_exact_price_qualifier(match, candidate_text: str) -> bool:
        before_number = candidate_text[max(0, match.start(1) - 32):match.start(1)]
        suffix = candidate_text[match.end():match.end() + 32]
        return (non_exact_price_before_number.search(before_number) is not None
                or non_exact_price_suffix.search(match.group(0)) is not None
                or non_exact_price_suffix.match(suffix) is not None)

    has_qualified_price = False

    def exclude_non_listing_or_track_qualifier(match):
        nonlocal has_qualified_price
        if linked_non_listing_price(match):
            return True
        has_qualified_price |= has_non_exact_price_qualifier(match, text)
        return False
    area_qualifiers = ('实用', '使用', '套内', '室内', '公摊', '占地', '赠送')
    area_prefixes = area_qualifiers + tuple(
        f'{qualifier}{separator}建筑'
        for qualifier in area_qualifiers for separator in ('', ' ')
    )
    area_labels = r'(?:建筑面积|建面|面积)'
    area_number = r'[0-9,]+(?:\.[0-9]+)?'
    area_units = r'(?:㎡|m²|平米|平方米|平方|平)'
    area_non_exact_qualifier = (
        r'(?:>=|<=|>|<|≥|≤|≧|≦|大约|约|大概|参考|估算|估计|预估|在|左右|上下|出头|附近|大于|超过|高于|多于|小于|低于|不满|'
        r'以上|以下|以内|不到|不足|不超过|不高于|不低于|至少|至多|最低|最高|'
        r'封顶|起步|起(?=$|[\s，,。；;：:、（）()])|[+＋])'
    )
    area_non_exact_suffix = (
        rf'\s*(?:[（(]\s*)?{area_non_exact_qualifier}(?:\s*[）)])?'
    )
    area_non_exact_qualifier_pattern = re.compile(area_non_exact_qualifier)
    area_prefix = _negative_label_prefixes(area_prefixes)
    area_label_pattern = (area_prefix
                         + rf'(?:{area_non_exact_qualifier}\s*[:：]?\s*)?'
                         + area_labels + r'\s*[:：]?\s*'
                         + r'(?:为\s*)?'
                         + rf'(?:{area_non_exact_qualifier}\s*[:：]?\s*)?'
                         + r'(?:为\s*)?')
    area_pattern = (area_label_pattern
                    + rf'({area_number})\s*{area_units}(?![方米])'
                    + rf'(?:{area_non_exact_suffix})?'
                    + rf'(?!\s*{range_separator}\s*{range_endpoint_start})')
    area_range_pattern = (
        area_label_pattern
        + rf'({area_number}\s*{area_units}?\s*{range_separator}\s*'
        + rf'{area_number}\s*{area_units})'
        + rf'(?:{area_non_exact_suffix})?')
    def has_non_exact_area_qualifier(match) -> bool:
        return area_non_exact_qualifier_pattern.search(match.group(0)) is not None
    # Prefer the semantic root with the strongest explicit listing evidence.
    class_root_names = {'houseInfo', 'house-info', 'content'}

    def candidate_roots():
        yield soup.find('main')
        for tag in soup.find_all('article'):
            ancestor = tag.parent
            while isinstance(ancestor, Tag):
                if ancestor.name == 'article':
                    break
                ancestor = ancestor.parent
            else:
                yield tag
        for tag in soup.descendants:
            if not isinstance(tag, Tag) or not class_root_names.intersection(tag.get('class') or ()):
                continue
            ancestor = tag.parent
            while isinstance(ancestor, Tag):
                if class_root_names.intersection(ancestor.get('class') or ()):
                    break
                ancestor = ancestor.parent
            else:
                yield tag

    conflicted_article_roots = {}

    def signal_count(tag: Tag, candidate_text: str, candidate_truncated: bool) -> int:
        def unique_match(pattern: str, *, numeric: bool = False, exclude_match=None):
            first_match = None
            first_key = None
            for match in re.finditer(pattern, candidate_text, re.IGNORECASE):
                if exclude_match is not None and exclude_match(match):
                    continue
                raw_value = match.group(1).strip()
                if numeric:
                    try:
                        key = Decimal(raw_value.replace(',', ''))
                    except InvalidOperation:
                        key = ('invalid', raw_value)
                else:
                    key = normalize_text_for_comparison(raw_value)
                if first_match is None:
                    first_match, first_key = match, key
                elif key != first_key:
                    return None, True
            return first_match, False

        community_match, multiple_community_matches = unique_match(community_pattern)
        area_match, multiple_area_matches = unique_match(area_pattern, numeric=True)
        area_range = re.search(area_range_pattern, candidate_text, re.IGNORECASE)
        exclude_linked_price = lambda match: is_linked_non_listing_price(match, candidate_text)
        price_match, multiple_price_matches = unique_match(
            price_pattern, numeric=True,
            exclude_match=lambda match: exclude_linked_price(match)
            or has_non_exact_price_qualifier(match, candidate_text))
        if tag.name == 'article' and multiple_price_matches:
            conflicted_article_roots[id(tag)] = (tag, candidate_text,
                                                  candidate_truncated)
        price_range = any(
            not exclude_linked_price(match)
            for match in re.finditer(price_range_pattern, candidate_text, re.IGNORECASE))
        score = sum((
            community_match is not None and not multiple_community_matches,
            area_match is not None and not multiple_area_matches and area_range is None
            and _number_str(area_match.group(1), 0, 20000, minimum_exclusive=True) is not None,
            price_match is not None and not multiple_price_matches and not price_range
            and _number_str(price_match.group(1), 0, 200000, minimum_exclusive=True) is not None,
        ))
        if score < 3 and tag.name == 'main' and tag.find('article') is not None:
            raw_community_match = re.search(community_pattern, candidate_text, re.IGNORECASE)
            raw_area_match = re.search(area_pattern, candidate_text, re.IGNORECASE)
            raw_price_match = next((match for match in re.finditer(
                price_pattern, candidate_text, re.IGNORECASE)
                if not exclude_linked_price(match)
                and not has_non_exact_price_qualifier(match, candidate_text)), None)
            score = sum((
                raw_community_match is not None,
                raw_area_match is not None
                and _number_str(raw_area_match.group(1), 0, 20000,
                                minimum_exclusive=True) is not None,
                raw_price_match is not None
                and _number_str(raw_price_match.group(1), 0, 200000,
                                minimum_exclusive=True) is not None,
            ))
        return score

    selected_candidate = None
    selected_score = -1
    equally_scored_candidates = []
    seen_candidate_ids = set()

    def is_descendant_root(root: Tag, candidate: Tag) -> bool:
        current = candidate.parent
        while isinstance(current, Tag):
            if current is root:
                return True
            current = current.parent
        return False

    for tag in candidate_roots():
        if tag is None or id(tag) in seen_candidate_ids:
            continue
        seen_candidate_ids.add(id(tag))
        if (selected_candidate is not None and selected_score == 3
                and is_descendant_root(selected_candidate[0], tag)):
            continue
        candidate_text, candidate_truncated = _normalize_text_prefix(
            _text_with_inline_boundaries(tag), MAX_VISIBLE_TEXT_CHARS)
        if not candidate_text.strip():
            continue
        score = signal_count(tag, candidate_text, candidate_truncated)
        if selected_candidate is None or score > selected_score:
            selected_candidate = (tag, candidate_text, candidate_truncated)
            selected_score = score
            equally_scored_candidates = [selected_candidate]
        elif score == selected_score:
            equally_scored_candidates.append((tag, candidate_text, candidate_truncated))
    scored_selection = selected_candidate
    if (selected_candidate is not None
            and class_root_names.intersection(selected_candidate[0].get('class') or ())):
        ancestor = selected_candidate[0].parent
        while isinstance(ancestor, Tag):
            if ancestor.name == 'article' and id(ancestor) in conflicted_article_roots:
                selected_candidate = conflicted_article_roots[id(ancestor)]
                break
            ancestor = ancestor.parent
    if selected_candidate is not None:
        main, text, text_truncated = selected_candidate
    else:
        main = soup.body or soup
        text, text_truncated = _normalize_text_prefix(
            _text_with_inline_boundaries(main), MAX_VISIBLE_TEXT_CHARS)
    warnings: list[str] = []
    if text_truncated:
        warnings.append('visible_text_truncated')
    if unresolved_inline_visibility:
        warnings.append('unresolved_inline_visibility')
    if unresolved_stylesheet_visibility:
        warnings.append('unresolved_stylesheet_visibility')

    source_listing_id = extract_source_id(source_url)
    source_url_id = source_listing_id
    head = soup.head
    canonical_ids = set()
    canonical_id_evidence = []
    og_url_id_evidence = []
    open_graph_title_values = {}
    canonical_id_count = 0
    canonical_id_mismatch = False

    def collect_canonical_id(canonical_url: str, evidence: list) -> None:
        nonlocal canonical_id_count, canonical_id_mismatch
        try:
            parts = urlsplit(canonical_url)
            safe_canonical_url = urlunsplit(parts._replace(query='', fragment=''))
            canonical_id = extract_source_id(safe_canonical_url)
        except ValueError:
            return
        if canonical_id:
            canonical_id_count += 1
            if source_listing_id and canonical_id != source_listing_id:
                canonical_id_mismatch = True
            if len(canonical_ids) < 2:
                canonical_ids.add(canonical_id)
            if len(evidence) < 20:
                path = urlsplit(safe_canonical_url).path
                id_start = path.rfind(canonical_id)
                id_segment_start = path.rfind('/', 0, id_start)
                segment_start = path.rfind('/', 0, id_segment_start)
                quote = path[segment_start:]
                start = quote.rfind(canonical_id)
                evidence.append({
                    'candidate_value': canonical_id,
                    'source': 'canonical_url',
                    'quote': quote,
                    'start_char': start,
                    'end_char': start + len(canonical_id),
                })

    if head:
        for tag in head.descendants:
            if not isinstance(tag, Tag):
                continue
            if tag.name == 'link':
                if (not any(re.fullmatch('canonical', token, re.IGNORECASE | re.ASCII)
                            for token in (tag.get('rel') or [])) or not tag.get('href')):
                    continue
                try:
                    collect_canonical_id(urljoin(source_url, tag['href'].strip()),
                                         canonical_id_evidence)
                except ValueError:
                    continue
            elif tag.name == 'meta':
                property_name = tag.get('property')
                if property_name == 'og:url' and tag.get('content'):
                    try:
                        collect_canonical_id(
                            urljoin(source_url, tag['content'].strip()), og_url_id_evidence)
                    except ValueError:
                        pass
                if str(property_name or '').strip().lower() == 'og:title':
                    title_value = tag.get('content')
                    if isinstance(title_value, str) and title_value.strip():
                        title_value = title_value.strip()
                        title_key = normalize_text_for_comparison(title_value)
                        if title_key in open_graph_title_values or len(open_graph_title_values) < 2:
                            open_graph_title_values.setdefault(title_key, title_value)
    canonical_id_evidence.extend(
        og_url_id_evidence[:max(0, 20 - len(canonical_id_evidence))])
    if source_listing_id and canonical_id_mismatch:
        source_listing_id = None
        warnings.append('canonical_source_id_mismatch')
    elif not source_listing_id and len(canonical_ids) == 1:
        source_listing_id = next(iter(canonical_ids))
    elif not source_listing_id and len(canonical_ids) > 1:
        warnings.append('canonical_source_id_mismatch')

    def open_graph_titles():
        yield from open_graph_title_values.values()

    def h1_titles():
        redundant_heading_ids = set()

        def mark_nested_heading_wrappers(tag: Tag) -> None:
            heading_chain = [tag]
            current = tag
            while True:
                only_child_tag = None
                for child in current.children:
                    if isinstance(child, Tag):
                        if id(child) not in textful_node_ids:
                            continue
                        if only_child_tag is not None:
                            only_child_tag = None
                            break
                        only_child_tag = child
                    elif (isinstance(child, NavigableString) and not isinstance(child, Comment)
                          and str(child).strip()):
                        only_child_tag = None
                        break
                if only_child_tag is None:
                    break
                current = only_child_tag
                if current.name == 'h1':
                    heading_chain.append(current)
            if len(heading_chain) > 1:
                redundant_heading_ids.update(id(heading) for heading in heading_chain[:-1])

        for tag in soup.descendants:
            if isinstance(tag, Tag) and tag.name == 'h1':
                if id(tag) in redundant_heading_ids:
                    continue
                mark_nested_heading_wrappers(tag)
                if id(tag) in redundant_heading_ids:
                    continue
                yield re.sub(r'\s+', ' ', _text_with_inline_boundaries(tag)).strip()

    def document_titles():
        for tag in head.descendants if head else ():
            if isinstance(tag, Tag) and tag.name == 'title':
                yield tag.get_text(' ', strip=True)

    title_candidates = (
        ('og:title', open_graph_titles()),
        ('h1', h1_titles()),
        ('head:title', document_titles()),
    )
    selected_title = None
    for source, values in title_candidates:
        unique_values = _unique_text_values(values)
        if len(unique_values) > 1:
            warnings.append(f'ambiguous_title_source:{source}')
        elif unique_values:
            selected_title = (source, unique_values[0][:500])
            break
    textful_node_ids.clear()
    title_source, title = selected_title if selected_title else (None, None)

    # Explicit labels are safer than a generic '365万' or '160㎡' somewhere on the page.
    field_evidence_scans = {}
    community, communities, field_evidence_scans['community_name'] = (
        _scan_field_evidence(community_pattern, text))
    if len(communities) > 1:
        warnings.append('multiple_community_mentions')
        community = None
    # A price printed without an explicit label is a weaker clue and is not promoted.
    price, prices, field_evidence_scans['asking_price_wan'] = (
        _scan_field_evidence(price_pattern, text, numeric=True,
                             exclude_match=exclude_non_listing_or_track_qualifier,
                             mention_metadata=lambda match: {
                                 'is_non_exact': has_non_exact_price_qualifier(match, text)}))
    if len(prices) > 1:
        warnings.append('multiple_price_mentions')
    if has_qualified_price:
        price = None
        warnings.append('non_exact_asking_price')
    area, areas, field_evidence_scans['area_sqm'] = (
        _scan_field_evidence(area_pattern, text, numeric=True,
                             mention_metadata=lambda match: {
                                 'is_non_exact': has_non_exact_area_qualifier(match)}))
    if len(areas) > 1:
        warnings.append('multiple_area_mentions')

    def merge_range_evidence(field: str, range_pattern: str, warning: str,
                             *, exclude_match=None,
                             mention_metadata=None) -> bool:
        range_values, _, range_evidence = _scan_field_evidence(
            range_pattern, text, exclude_match=exclude_match,
            mention_metadata=mention_metadata)
        if not range_values:
            return False
        existing = field_evidence_scans[field]
        mentions = sorted(existing['mentions'] + range_evidence['mentions'],
                          key=lambda mention: mention['start_char'])
        mention_count = existing['mention_count'] + range_evidence['mention_count']
        field_evidence_scans[field] = {
            'mentions': mentions[:20],
            'mention_count': mention_count,
            'mentions_truncated': mention_count > min(len(mentions), 20),
        }
        if warning not in warnings:
            warnings.append(warning)
        return True

    if merge_range_evidence('area_sqm', area_range_pattern, 'multiple_area_mentions',
                            mention_metadata=lambda match: {
                                'is_non_exact': has_non_exact_area_qualifier(match)}):
        area = None
    if merge_range_evidence('asking_price_wan', price_range_pattern,
                            'multiple_price_mentions',
                            exclude_match=linked_non_listing_price,
                            mention_metadata=lambda match: {
                                'is_non_exact': has_non_exact_price_qualifier(match, text)}):
        price = None
        if (any(mention.get('is_non_exact') is True
                for mention in field_evidence_scans['asking_price_wan']['mentions'])
                and 'non_exact_asking_price' not in warnings):
            warnings.append('non_exact_asking_price')
    bedrooms_pattern = r'(?:户型|房型)\s*[:：]?\s*(?<!\d)(\d{1,2})(?!\d)\s*室'
    bedrooms, bedroom_mentions, field_evidence_scans['bedrooms'] = (
        _scan_field_evidence(bedrooms_pattern, text, numeric=True))
    if len(bedroom_mentions) > 1:
        warnings.append('multiple_bedrooms_mentions')
    bedroom_count = int(bedrooms) if bedrooms else None
    if bedroom_count is not None and bedroom_count > 20:
        bedroom_count = None
        warnings.append('invalid_bedrooms_mentions')
    district_pattern = r'(?:所在区域|行政区|区域)\s*[:：]?\s*(' + '|'.join(DISTRICTS) + ')'
    district, district_mentions, field_evidence_scans['district'] = (
        _scan_field_evidence(district_pattern, text))
    if len(district_mentions) > 1:
        warnings.append('multiple_district_mentions')
    floor_pattern = (rf'(?<!总)楼层\s*[:：]?\s*'
                     rf'({free_text_value_chars}{{2,120}}?)'
                     + free_text_value_end)
    floor, floor_mentions, field_evidence_scans['floor_text'] = (
        _scan_field_evidence(floor_pattern, text))
    if len(floor_mentions) > 1:
        warnings.append('multiple_floor_mentions')
    decoration_pattern = (rf'(?:装修情况|装修状况|装修状态|装修)\s*[:：]?\s*'
                          rf'({free_text_value_chars}{{2,120}}?)'
                          + free_text_value_end)
    decoration, decoration_mentions, field_evidence_scans['decoration'] = (
        _scan_field_evidence(decoration_pattern, text))
    if len(decoration_mentions) > 1:
        warnings.append('multiple_decoration_mentions')

    def root_field_values(candidate_text: str):
        price_exclusion = lambda match: is_linked_non_listing_price(match, candidate_text)
        patterns = {
            'community_name': (community_pattern, False, None),
            'district': (district_pattern, False, None),
            'area_sqm': (area_pattern, True, area_range_pattern),
            'asking_price_wan': (price_pattern, True, price_range_pattern),
            'bedrooms': (bedrooms_pattern, True, None),
            'floor_text': (floor_pattern, False, None),
            'decoration': (decoration_pattern, False, None),
        }
        values_by_field = {}
        for field, (pattern, numeric, range_pattern) in patterns.items():
            exclude = price_exclusion if field == 'asking_price_wan' else None
            _, values, _ = _scan_field_evidence(
                pattern, candidate_text, numeric=numeric, exclude_match=exclude)
            range_values = []
            if range_pattern:
                _, range_values, _ = _scan_field_evidence(
                    range_pattern, candidate_text, exclude_match=exclude)
            if numeric:
                normalized = {Decimal(value.replace(',', '')) for value in values
                              if isinstance(value, str) and re.fullmatch(
                                  NUMERIC_TEXT_PATTERN, value)}
                normalized.update(('range', value) for value in range_values)
            else:
                normalized = {normalize_text_for_comparison(value) for value in values}
                normalized.update(('range', value) for value in range_values)
            values_by_field[field] = normalized
        return values_by_field

    def roots_are_independent(left: Tag, right: Tag) -> bool:
        for ancestor, descendant in ((left, right), (right, left)):
            current = descendant.parent
            while isinstance(current, Tag):
                if current is ancestor:
                    return False
                current = current.parent
        return True

    selected_root = scored_selection[0] if scored_selection else None
    independent_ties = [candidate for candidate in equally_scored_candidates
                        if candidate[0] is selected_root or
                        roots_are_independent(selected_root, candidate[0])]
    conflicting_root_fields = set()
    if len(independent_ties) > 1:
        candidate_root_values = [root_field_values(candidate[1])
                                 for candidate in independent_ties]
        for field in candidate_root_values[0]:
            nonempty_values = [values[field] for values in candidate_root_values
                               if values[field]]
            if nonempty_values and any(
                    values != nonempty_values[0] for values in nonempty_values[1:]):
                conflicting_root_fields.add(field)

    if conflicting_root_fields:
        evidence_roots = [selected_candidate]
        evidence_roots.extend(
            candidate for candidate in independent_ties
            if candidate[0] is not selected_root
            and roots_are_independent(selected_candidate[0], candidate[0]))
        text = '\n'.join(candidate[1] for candidate in evidence_roots)
        text_truncated = any(candidate[2] for candidate in evidence_roots)
        if text_truncated and 'visible_text_truncated' not in warnings:
            warnings.append('visible_text_truncated')

        evidence_patterns = {
            'community_name': (community_pattern, False, None),
            'district': (district_pattern, False, None),
            'area_sqm': (area_pattern, True, area_range_pattern),
            'asking_price_wan': (price_pattern, True, price_range_pattern),
            'bedrooms': (bedrooms_pattern, True, None),
            'floor_text': (floor_pattern, False, None),
            'decoration': (decoration_pattern, False, None),
        }
        warning_names = {
            'community_name': 'multiple_community_mentions',
            'district': 'multiple_district_mentions',
            'area_sqm': 'multiple_area_mentions',
            'asking_price_wan': 'multiple_price_mentions',
            'bedrooms': 'multiple_bedrooms_mentions',
            'floor_text': 'multiple_floor_mentions',
            'decoration': 'multiple_decoration_mentions',
        }
        for field in conflicting_root_fields:
            pattern, numeric, range_pattern = evidence_patterns[field]
            price_exclusion = lambda match: is_linked_non_listing_price(match, text)
            exclude = price_exclusion if field == 'asking_price_wan' else None
            mention_metadata = None
            if field == 'area_sqm':
                mention_metadata = lambda match: {
                    'is_non_exact': has_non_exact_area_qualifier(match)}
            if field == 'asking_price_wan':
                mention_metadata = lambda match: {
                    'is_non_exact': has_non_exact_price_qualifier(match, text)}
            _, _, evidence = _scan_field_evidence(
                pattern, text, numeric=numeric, exclude_match=exclude,
                mention_metadata=mention_metadata)
            if range_pattern:
                range_mention_metadata = None
                if field == 'asking_price_wan':
                    range_mention_metadata = lambda match: {
                        'is_non_exact': has_non_exact_price_qualifier(match, text)}
                elif field == 'area_sqm':
                    range_mention_metadata = lambda match: {
                        'is_non_exact': has_non_exact_area_qualifier(match)}
                _, _, range_evidence = _scan_field_evidence(
                    range_pattern, text, exclude_match=exclude,
                    mention_metadata=range_mention_metadata)
                evidence['mentions'] = sorted(
                    evidence['mentions'] + range_evidence['mentions'],
                    key=lambda mention: mention['start_char'])[:20]
                evidence['mention_count'] += range_evidence['mention_count']
                evidence['mentions_truncated'] = (
                    evidence['mention_count'] > len(evidence['mentions']))
            field_evidence_scans[field] = evidence
            warning = warning_names[field]
            if warning not in warnings:
                warnings.append(warning)

    if any(mention.get('is_non_exact') is True
           for mention in field_evidence_scans['area_sqm']['mentions']):
        area = None
        warnings.append('non_exact_area_sqm')

    fields = {
        'source_listing_id': source_listing_id,
        'title': title,
        'community_name': community,
        'district': district,
        'area_sqm': _number_str(area, 0, 20000, minimum_exclusive=True),
        'bedrooms': bedroom_count,
        'floor_text': floor,
        'decoration': decoration,
        'asking_price_wan': _number_str(price, 0, 200000, minimum_exclusive=True),
        'listing_url': source_url,
        'evidence_excerpt': text[:1000],
    }
    for field in conflicting_root_fields:
        fields[field] = None
    for field, raw_value in (('area_sqm', area), ('asking_price_wan', price)):
        if raw_value is not None and _requires_subcent_correction(raw_value):
            warnings.append(f'numeric_precision_requires_correction:{field}')
    field_evidence = {}
    if title is not None:
        field_evidence['title'] = {
            'value': title,
            'source': title_source,
            'quote': title,
        }
    id_mentions = []
    if source_url_id:
        start = source_url.rfind(source_url_id)
        id_mentions.append({
            'candidate_value': source_url_id,
            'source': 'source_url',
            'quote': source_url,
            'start_char': start,
            'end_char': start + len(source_url_id),
        })
    id_mentions.extend(canonical_id_evidence[:20 - len(id_mentions)])
    id_mention_count = int(source_url_id is not None) + canonical_id_count
    if id_mentions:
        field_evidence['source_listing_id'] = {
            'value': fields['source_listing_id'],
            'mentions': id_mentions,
            'mention_count': id_mention_count,
            'mentions_truncated': id_mention_count > len(id_mentions),
        }
    for field, evidence in field_evidence_scans.items():
        if evidence['mention_count']:
            field_evidence[field] = {'value': fields[field], **evidence}
    fields['confidence_status'] = 'not_calibrated'
    fields['field_evidence'] = field_evidence
    for key in ('source_listing_id', 'community_name', 'area_sqm', 'asking_price_wan'):
        if fields[key] is None:
            warnings.append('missing_' + key)
    warnings.append('human_review_required')
    digest = hashlib.sha256(html_bytes).hexdigest()
    return ParseResult(fields, warnings, digest)
