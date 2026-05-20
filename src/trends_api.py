import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from typing import Iterable, List, Optional

import requests

REQUEST_TIMEOUT = 5
MAX_RESULTS = 100

SOURCE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

RSS_SOURCES = [
    ("Ukrinform", "https://www.ukrinform.ua/rss/block-lastnews"),
    ("Suspilne", "https://suspilne.media/rss/"),
    ("Hromadske", "https://hromadske.ua/rss"),
    ("Ukrainska Pravda", "https://www.pravda.com.ua/rss/view_news/"),
    ("TSN", "https://tsn.ua/rss/full.rss"),
    ("NV", "https://nv.ua/rss/all.xml"),
]

REDDIT_SOURCES = [
    ("Reddit /r/ukraine hot", "https://www.reddit.com/r/ukraine/hot.json?limit=25&t=day"),
    ("Reddit /r/ukraine top", "https://www.reddit.com/r/ukraine/top.json?limit=25&t=day"),
    ("Reddit /r/ukraina hot", "https://www.reddit.com/r/ukraina/hot.json?limit=25&t=day"),
    (
        "Reddit search Ukraine",
        "https://www.reddit.com/search.json?q=(Ukraine%20OR%20%D0%A3%D0%BA%D1%80%D0%B0%D1%97%D0%BD%D0%B0%20OR%20%D0%9A%D0%B8%D1%97%D0%B2%20OR%20Kyiv)&sort=hot&t=day&limit=25",
    ),
]

SOCIAL_SOURCES = [
    ("TikTok #ukraine", "https://www.tiktok.com/tag/ukraine"),
    ("TikTok #kyiv", "https://www.tiktok.com/tag/kyiv"),
    ("Instagram #ukraine", "https://www.instagram.com/explore/tags/ukraine/"),
    ("Instagram #kyiv", "https://www.instagram.com/explore/tags/kyiv/"),
]


@dataclass(frozen=True)
class TrendCandidate:
    title: str
    source: str
    url: str = ""
    score: float = 0.0
    published_at: Optional[datetime] = None


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    value = value.strip()
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        pass

    for pattern in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(value, pattern)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            continue

    return None


def _normalize_title(title: str) -> str:
    normalized = re.sub(r"\s+", " ", title.lower()).strip()
    normalized = re.sub(r"[^\w\s\u0400-\u04FF\u0590-\u05FF\-]", "", normalized)
    return normalized


def _clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = title.replace("\u00a0", " ")
    return title


def _recency_bonus(published_at: Optional[datetime]) -> float:
    if not published_at:
        return 0.0

    age_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600.0
    if age_hours <= 1:
        return 20.0
    if age_hours <= 6:
        return 15.0
    if age_hours <= 24:
        return 10.0
    if age_hours <= 72:
        return 5.0
    return 0.0


def _source_weight(source: str) -> float:
    if source.startswith("RSS"):
        return 100.0
    if source.startswith("Reddit"):
        return 85.0
    if source.startswith("TikTok"):
        return 75.0
    if source.startswith("Instagram"):
        return 70.0
    return 50.0


def _request_text(url: str, *, headers: Optional[dict] = None) -> str:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={**SOURCE_HEADERS, **(headers or {})},
    )
    response.raise_for_status()
    return response.text


def _request_json(url: str, *, headers: Optional[dict] = None) -> dict:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={**SOURCE_HEADERS, **(headers or {})},
    )
    response.raise_for_status()
    return response.json()


def _fetch_rss_candidates(source_name: str, url: str, limit: int = 25) -> List[TrendCandidate]:
    html = _request_text(
        url,
        headers={
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )

    root = ET.fromstring(html)
    items = root.findall("./channel/item") or root.findall(".//item")

    candidates: List[TrendCandidate] = []
    for index, item in enumerate(items):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue

        link = (item.findtext("link") or "").strip()
        published_at = _parse_datetime(item.findtext("pubDate") or item.findtext("published"))
        score = _source_weight(f"RSS {source_name}") + _recency_bonus(published_at) + max(0.0, 10.0 - index)
        candidates.append(
            TrendCandidate(
                title=_clean_title(title),
                source=f"RSS {source_name}",
                url=link,
                score=score,
                published_at=published_at,
            )
        )

        if len(candidates) >= limit:
            break

    return candidates


def _fetch_reddit_candidates(source_name: str, url: str, limit: int = 25) -> List[TrendCandidate]:
    payload = _request_json(
        url,
        headers={
            "Accept": "application/json,text/plain,*/*",
        },
    )

    posts = payload.get("data", {}).get("children", [])
    candidates: List[TrendCandidate] = []
    for index, post in enumerate(posts):
        data = post.get("data", {}) if isinstance(post, dict) else {}
        title = _clean_title(str(data.get("title", "")).strip())
        if not title or len(title) < 3 or len(title) > 180:
            continue

        permalink = str(data.get("permalink", "")).strip()
        link = f"https://www.reddit.com{permalink}" if permalink else ""
        published_at = None
        created_utc = data.get("created_utc")
        if isinstance(created_utc, (int, float)):
            published_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)

        score = _source_weight(source_name) + _recency_bonus(published_at) + max(0.0, 10.0 - index)
        candidates.append(
            TrendCandidate(
                title=title,
                source=source_name,
                url=link,
                score=score,
                published_at=published_at,
            )
        )

        if len(candidates) >= limit:
            break

    return candidates


def _extract_json_strings(html: str, patterns: Iterable[str]) -> List[str]:
    values: List[str] = []
    seen = set()

    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE | re.DOTALL):
            raw_value = match.group(1)
            try:
                value = json.loads(f'"{raw_value}"')
            except Exception:
                continue

            value = _clean_title(value)
            if len(value) < 8 or len(value) > 180:
                continue

            normalized = _normalize_title(value)
            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            values.append(value)

    return values


def _fetch_tiktok_candidates(source_name: str, url: str, limit: int = 25) -> List[TrendCandidate]:
    html = _request_text(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.tiktok.com/",
        },
    )

    patterns = [
        r'"desc":"((?:\\.|[^"\\]){8,220})"',
        r'"itemTitle":"((?:\\.|[^"\\]){8,220})"',
        r'"shareTitle":"((?:\\.|[^"\\]){8,220})"',
    ]
    titles = _extract_json_strings(html, patterns)

    return [
        TrendCandidate(title=title, source=source_name, score=_source_weight(source_name) + max(0.0, 10.0 - index))
        for index, title in enumerate(titles[:limit])
    ]


def _fetch_instagram_candidates(source_name: str, url: str, limit: int = 25) -> List[TrendCandidate]:
    html = _request_text(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.instagram.com/",
        },
    )

    patterns = [
        r'"caption":"((?:\\.|[^"\\]){8,220})"',
        r'"edge_media_to_caption":\{"edges":\[\{"node":\{"text":"((?:\\.|[^"\\]){8,220})"',
        r'"text":"((?:\\.|[^"\\]){8,220})"',
    ]
    titles = _extract_json_strings(html, patterns)

    return [
        TrendCandidate(title=title, source=source_name, score=_source_weight(source_name) + max(0.0, 10.0 - index))
        for index, title in enumerate(titles[:limit])
    ]


def _score_and_merge_candidates(candidates: List[TrendCandidate], limit: int = MAX_RESULTS) -> List[TrendCandidate]:
    if not candidates:
        return []

    normalized_counts = Counter(_normalize_title(candidate.title) for candidate in candidates if candidate.title)
    sorted_candidates = sorted(candidates, key=lambda candidate: candidate.score, reverse=True)

    merged: List[TrendCandidate] = []
    seen_normalized: List[str] = []

    for candidate in sorted_candidates:
        normalized = _normalize_title(candidate.title)
        if not normalized:
            continue

        if any(
            normalized == existing or SequenceMatcher(None, normalized, existing).ratio() >= 0.9
            for existing in seen_normalized
        ):
            continue

        bonus = max(0, normalized_counts[normalized] - 1) * 4
        merged.append(
            TrendCandidate(
                title=candidate.title,
                source=candidate.source,
                url=candidate.url,
                score=candidate.score + bonus,
                published_at=candidate.published_at,
            )
        )
        seen_normalized.append(normalized)

        if len(merged) >= limit:
            break

    return merged


def _collect_trends(limit: int = MAX_RESULTS) -> List[TrendCandidate]:
    sources = []
    errors = []

    def fetch_rss(source_name, url):
        try:
            return _fetch_rss_candidates(source_name, url)
        except Exception as exc:
            errors.append(f"RSS {source_name}: {type(exc).__name__}")
            return []

    def fetch_reddit(source_name, url):
        try:
            return _fetch_reddit_candidates(source_name, url)
        except Exception as exc:
            errors.append(f"{source_name}: {type(exc).__name__}")
            return []

    def fetch_social(source_name, url):
        try:
            if source_name.startswith("TikTok"):
                return _fetch_tiktok_candidates(source_name, url)
            else:
                return _fetch_instagram_candidates(source_name, url)
        except Exception as exc:
            errors.append(f"{source_name}: {type(exc).__name__}")
            return []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []

        for source_name, url in RSS_SOURCES:
            futures.append(executor.submit(fetch_rss, source_name, url))

        for source_name, url in REDDIT_SOURCES:
            futures.append(executor.submit(fetch_reddit, source_name, url))

        for source_name, url in SOCIAL_SOURCES:
            futures.append(executor.submit(fetch_social, source_name, url))

        for future in as_completed(futures, timeout=10):
            try:
                result = future.result(timeout=1)
                sources.extend(result)
            except Exception:
                pass

    merged = _score_and_merge_candidates(sources, limit=limit)
    if merged:
        return merged

    error_text = f"{len(errors)} sources failed" if errors else "no sources returned data"
    raise RuntimeError(f"Could not fetch trends from available sources: {error_text}")


def _fetch_trends_via_rss() -> List[str]:
    """Читає Google Trends RSS для України."""
    response = requests.get(
        "https://trends.google.com/trending/rss?geo=UA",
        timeout=25,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    response.raise_for_status()

    root = ET.fromstring(response.text)
    items = root.findall("./channel/item/title")
    trends = [item.text.strip() for item in items if item.text][:5]
    if not trends:
        raise RuntimeError("Google Trends RSS не повернув елементів")
    return trends


def get_top_daily_trends(limit: int = 5) -> List[str]:
    """Топ 5 трендів для головного екрану — тільки Google Trends RSS, швидко."""
    try:
        rss_trends = _fetch_trends_via_rss()
        if rss_trends:
            return rss_trends[:limit]
    except Exception:
        pass
    return []


def get_all_trends_full(limit: int = 100) -> List[str]:
    """До 100 трендів з усіх джерел для модального вікна."""
    # Спочатку Google Trends (найавторитетніше джерело)
    google_trends = []
    try:
        google_trends = _fetch_trends_via_rss()
    except Exception:
        pass

    # Потім всі інші джерела паралельно
    try:
        collected = _collect_trends(limit)
        titles = [t.title for t in collected]

        # Google Trends ставимо на перші місця, решту — далі
        seen = set(_normalize_title(t) for t in google_trends)
        merged = list(google_trends)
        for title in titles:
            if _normalize_title(title) not in seen:
                merged.append(title)
                seen.add(_normalize_title(title))
            if len(merged) >= limit:
                break

        return merged[:limit]
    except Exception:
        # Якщо всі джерела впали — повертаємо хоча б Google Trends
        return google_trends[:limit]