# app/news_normalizer.py
import re
import html
from bs4 import BeautifulSoup

MAX_TITLE_LEN = 90
MAX_SUMMARY_LEN = 180

def _strip_html(s: str | None) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = s.replace("<br>", ". ").replace("<br/>", ". ").replace("<br />", ". ")
    text = BeautifulSoup(s, "html.parser").get_text(" ")
    return re.sub(r"\s+", " ", text).strip()

def _clean_title(title: str) -> str:
    t = title
    # " ... - 매체명" 꼬리 제거
    t = re.sub(r"\s*-\s*[^\-]{2,40}$", "", t)
    # [속보], (영상) 등 접두 태그 제거
    t = re.sub(r"^\s*[\[\(](속보|영상|종합|단독|포토|르포|Q&A|인터뷰)[\]\)]\s*", "", t, flags=re.IGNORECASE)
    # 구분자 뒤 꼬리 제거
    t = re.split(r"\s[|/]\s", t)[0]
    # 양끝 기호
    t = re.sub(r"^[\-–—~\s]+|[\-–—~\s]+$", "", t)
    if len(t) > MAX_TITLE_LEN:
        t = t[:MAX_TITLE_LEN].rstrip() + "…"
    return t

NOISE_PATTERNS = [
    r"기사원문\s*보기.*$",
    r"자세히\s*보기.*$",
    r"앱에서\s*보기.*$",
    r"네이버\s*뉴스.*$",
    r"ⓒ.*?무단전재.*$",
    r"사진\s*=\s*.*$",
    r"▶.*$",
    r"■.*$",
    r"※.*$",
    r"더보기.*$",
]
NOISE_REGEX = re.compile("|".join(NOISE_PATTERNS))

def _first_sentence(s: str) -> str:
    # 한국어/영문 섞인 문장 첫 문장만
    # 우선 '다.' 기준, 없으면 '. ' 기준
    if "다. " in s:
        return s.split("다. ")[0] + "다."
    if ". " in s:
        return s.split(". ")[0] + "."
    return s

def _clean_summary(summary: str) -> str:
    s = _strip_html(summary)
    s = NOISE_REGEX.sub("", s).strip()
    s = _first_sentence(s)
    # 괄호만 남은 꼬리 제거
    s = re.sub(r"\(\s*\)$|\[\s*\]$|\{\s*\}$", "", s).strip()
    if len(s) > MAX_SUMMARY_LEN:
        s = s[:MAX_SUMMARY_LEN].rstrip() + "…"
    return s

def normalize_item(raw: dict, country: str) -> dict:
    title = _clean_title(_strip_html(raw.get("title") or ""))
    summary_raw = raw.get("summary") or raw.get("description") or ""
    summary = _clean_summary(summary_raw)
    link = raw.get("link")
    published = raw.get("published") or raw.get("updated") or raw.get("pubDate")
    return {
        "title": title,
        "summary": summary,
        "link": link,
        "published": published,
        "country": country,
        "source_feed": raw.get("source_feed"),
    }

def dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for x in items:
        k = x.get("link") or x.get("title")
        if k and k not in seen:
            out.append(x)
            seen.add(k)
    return out
