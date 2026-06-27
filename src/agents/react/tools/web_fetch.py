"""web_fetch tool: fetch a URL and return readable text.

This is the tool that closes the snippet-only gap of test-smith's
existing pipeline. It can be aimed at a specific keyword via the
`find` argument; when present, the tool returns the chunks of text
that contain the keyword (with surrounding context) instead of just
the page head.
"""

from __future__ import annotations

import io
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .base import Tool, ToolError, ToolResult

# PDF parsing is optional. We try pypdf first; if unavailable, fall back to
# the existing "PDF not supported" message.
try:
    from pypdf import PdfReader as _PdfReader
except ImportError:  # pragma: no cover — dep is present in test-smith
    _PdfReader = None

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    # Several anti-bot stacks (Cloudflare, BNFA, etc.) reject requests that
    # carry only a User-Agent — the absence of an Accept / Accept-Language /
    # Accept-Encoding header is a strong bot signal. Include the headers a
    # real browser would send so we don't get cargo-culted 403s.
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,ja;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

_STRIP_TAGS = ("script", "style", "noscript", "header", "footer", "nav", "aside", "form")


def _html_to_text(html: str) -> tuple[str, str]:
    """Return (title, plain_text) for an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    for tag_name in _STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    text = soup.get_text(separator="\n")
    # Collapse runs of blank lines but preserve paragraph breaks.
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return title, text.strip()


def _slice_around_keyword(
    text: str,
    keyword: str,
    window_before: int = 400,
    window_after: int = 6000,
) -> list[str]:
    """Return text windows containing the keyword (case-insensitive).

    The window is intentionally **asymmetric**: most TOC / index style
    keywords (``Sommaire``, ``目次``, ``Contents``, ``Table des matières``)
    appear at the *head* of the section the caller actually wants, with
    the useful body following the keyword. A symmetric window wastes
    half its budget on the boilerplate that came before the keyword.
    """
    if not keyword:
        return []
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    chunks: list[str] = []
    seen_ranges: list[tuple[int, int]] = []
    for match in pattern.finditer(text):
        start = max(0, match.start() - window_before)
        end = min(len(text), match.end() + window_after)
        # Merge with previous if overlapping.
        if seen_ranges and start <= seen_ranges[-1][1]:
            prev_start, _prev_end = seen_ranges[-1]
            seen_ranges[-1] = (prev_start, end)
        else:
            seen_ranges.append((start, end))
    for start, end in seen_ranges:
        chunks.append(text[start:end])
    return chunks


def _pdf_to_text(pdf_bytes: bytes, max_pages: int = 30) -> tuple[str, str]:
    """Return (title, plain_text) for a PDF byte stream.

    Reading is capped at ``max_pages`` to keep extraction fast; for a
    book PDF we mainly want the front-matter (TOC) which is in the first
    few pages.
    """
    if _PdfReader is None:
        raise ToolError(
            "PDF parsing requires the `pypdf` package, which is not installed."
        )
    reader = _PdfReader(io.BytesIO(pdf_bytes))
    title = ""
    try:
        meta = reader.metadata
        if meta and meta.title:
            title = str(meta.title).strip()
    except Exception:  # pragma: no cover — metadata is best-effort
        title = ""
    pages: list[str] = []
    for i, page in enumerate(reader.pages):
        if i >= max_pages:
            break
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # pragma: no cover — bad pages are skipped
            continue
    text = "\n\n".join(p.strip() for p in pages if p.strip())
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    return title, text.strip()


class WebFetchTool(Tool):
    def __init__(self, timeout_seconds: float = 20.0, max_chars: int = 16000):
        self._timeout = timeout_seconds
        self._default_max_chars = max_chars

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return (
            "Fetch a URL and return readable text. Use this to read past "
            "search snippets when you need the actual page content (e.g. a "
            "table of contents, full article body, primary source). Optional "
            "'find' parameter narrows the returned text to chunks containing "
            "that keyword."
        )

    @property
    def input_schema(self) -> str:
        return (
            '{"url": "https://...", '
            '"find": "<optional keyword, e.g. \'sommaire\' or \'目次\'>", '
            '"max_chars": 8000}'
        )

    def run(self, args: dict[str, Any]) -> ToolResult:
        url = (args.get("url") or "").strip()
        if not url:
            raise ToolError("web_fetch requires a 'url' argument")
        find = (args.get("find") or "").strip()
        max_chars = int(args.get("max_chars") or self._default_max_chars)

        try:
            with httpx.Client(
                headers=_DEFAULT_HEADERS,
                follow_redirects=True,
                timeout=self._timeout,
            ) as client:
                response = client.get(url)
        except httpx.HTTPError as e:
            raise ToolError(f"fetch failed for {url}: {e}") from e

        if response.status_code >= 400:
            raise ToolError(
                f"fetch failed for {url}: HTTP {response.status_code}"
            )

        content_type = response.headers.get("content-type", "").lower()
        is_pdf = "pdf" in content_type or url.lower().endswith(".pdf")
        if is_pdf:
            if _PdfReader is None:
                return ToolResult(
                    observation=(
                        f"URL is a PDF but the pypdf parser is not available.\n"
                        f"URL: {url}\n"
                        f"Consider searching for an HTML mirror."
                    )
                )
            try:
                title, text = _pdf_to_text(response.content)
            except ToolError as e:
                raise e
            except Exception as e:  # pragma: no cover — malformed PDFs
                raise ToolError(f"failed to parse PDF at {url}: {e}") from e
        elif "html" in content_type or "xml" in content_type or "text" in content_type:
            title, text = _html_to_text(response.text)
        else:
            return ToolResult(
                observation=(
                    f"URL returned non-text content-type: {content_type}. "
                    f"Skipping body extraction.\nURL: {url}"
                )
            )
        header = f"Fetched: {url}\nTitle: {title or '(no title)'}\n" + ("-" * 60)

        if find:
            chunks = _slice_around_keyword(text, find)
            if not chunks:
                preview = text[: max_chars // 2]
                body = (
                    f"Keyword '{find}' not found on page. Showing first "
                    f"{len(preview)} chars instead:\n\n{preview}"
                )
            else:
                joined = "\n\n— — —\n\n".join(chunks)
                if len(joined) > max_chars:
                    joined = joined[:max_chars] + "\n…[truncated]"
                body = (
                    f"Found {len(chunks)} section(s) containing '{find}':\n\n{joined}"
                )
        else:
            body = text[:max_chars]
            if len(text) > max_chars:
                body += "\n…[truncated]"

        return ToolResult(observation=f"{header}\n{body}")
