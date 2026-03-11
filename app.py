from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from html import unescape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, List
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

WEB_DIR = Path(__file__).parent / "web"
TRANSCRIPT_API_BASE = "https://www.youtube-transcript.io/api"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with",
    "this", "or", "if", "about", "into", "you", "your", "they", "their", "we", "our", "i", "me",
}


@dataclass
class SummaryResult:
    transcript: str
    short_summary: str
    long_summary: str
    short_read_minutes: int
    long_read_minutes: int


def extract_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")

    if host == "youtu.be":
        return parsed.path.lstrip("/") or None

    if host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/", 2)[2]

    return None


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_sentences(text: str) -> List[str]:
    candidates = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in candidates if len(s.strip()) > 20]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def sentence_score(sentence: str, frequencies: Counter, index: int, total_sentences: int) -> float:
    words = [w for w in tokenize(sentence) if w not in STOPWORDS]
    if not words:
        return 0.0

    lexical = sum(frequencies[w] for w in words) / len(words)
    position_weight = 1.0 + (0.15 if index < max(1, int(total_sentences * 0.15)) else 0)
    length_penalty = 1 / (1 + abs(len(words) - 20) / 30)
    return lexical * position_weight * length_penalty


def summarize_text(transcript: str, min_words: int, max_words: int) -> str:
    sentences = split_sentences(transcript)
    if not sentences:
        return ""

    frequencies = Counter(w for w in tokenize(transcript) if w not in STOPWORDS and len(w) > 2)
    scored = [
        (sentence_score(sentence, frequencies, idx, len(sentences)), idx, sentence)
        for idx, sentence in enumerate(sentences)
    ]
    scored.sort(key=lambda item: item[0], reverse=True)

    selected = []
    total_words = 0
    for _, idx, sentence in scored:
        word_count = len(tokenize(sentence))
        if total_words + word_count > max_words:
            continue
        selected.append((idx, sentence))
        total_words += word_count
        if total_words >= min_words:
            break

    if not selected:
        selected = [(idx, sentence) for idx, sentence in enumerate(sentences[: min(5, len(sentences))])]

    selected.sort(key=lambda item: item[0])
    return " ".join(sentence for _, sentence in selected)


def minutes_for_words(word_count: int) -> int:
    return max(1, math.ceil(word_count / 200))


def fetch_url(url: str, headers: dict[str, str] | None = None) -> str:
    req_headers = {"User-Agent": "Mozilla/5.0"}
    if headers:
        req_headers.update(headers)
    req = Request(url, headers=req_headers)
    with urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_transcript_from_api_payload(payload: Any) -> str:
    if isinstance(payload, str):
        return clean_text(payload)

    if isinstance(payload, dict):
        for key in ("transcript", "text", "content"):
            candidate = payload.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return clean_text(candidate)
        for key in ("segments", "captions", "items", "data"):
            candidate = payload.get(key)
            if isinstance(candidate, list):
                joined = [
                    str(item.get("text", "")).strip()
                    for item in candidate
                    if isinstance(item, dict)
                ]
                if any(joined):
                    return clean_text(" ".join(joined))
    if isinstance(payload, list):
        joined = [
            str(item.get("text", "")).strip()
            for item in payload
            if isinstance(item, dict)
        ]
        if any(joined):
            return clean_text(" ".join(joined))

    return ""


def fetch_transcript_from_api(video_url: str, video_id: str) -> str:
    token = os.environ.get("YOUTUBE_TRANSCRIPT_API_TOKEN", "").strip()
    if not token:
        return ""

    endpoints = [
        f"{TRANSCRIPT_API_BASE}?{urlencode({'url': video_url})}",
        f"{TRANSCRIPT_API_BASE}?{urlencode({'video_id': video_id})}",
        f"{TRANSCRIPT_API_BASE}/{video_id}",
    ]
    headers_variants = [
        {"Authorization": f"Bearer {token}", "Accept": "application/json"},
        {"x-api-key": token, "Accept": "application/json"},
        {"apikey": token, "Accept": "application/json"},
    ]

    for endpoint in endpoints:
        for headers in headers_variants:
            try:
                raw = fetch_url(endpoint, headers=headers)
                payload = json.loads(raw)
                transcript = extract_transcript_from_api_payload(payload)
                if transcript:
                    return transcript
            except Exception:
                continue

    return ""


def extract_caption_base_url(video_html: str) -> str | None:
    marker = '"captionTracks":'
    start = video_html.find(marker)
    if start == -1:
        return None

    snippet = video_html[start : start + 12000]
    match = re.search(r'"baseUrl":"(https:[^"]+)"', snippet)
    if not match:
        return None

    return unquote(match.group(1)).replace("\\u0026", "&")


def parse_timedtext_xml(xml: str) -> str:
    parts = re.findall(r"<text[^>]*>(.*?)</text>", xml, flags=re.DOTALL)
    if not parts:
        return ""
    cleaned = [clean_text(unescape(p)) for p in parts]
    return clean_text(" ".join(cleaned))


def fetch_transcript_with_fallback(video_url: str, video_id: str) -> str:
    html = fetch_url(f"https://www.youtube.com/watch?v={video_id}")
    caption_url = extract_caption_base_url(html)
    if not caption_url:
        return ""

    xml = fetch_url(caption_url)
    transcript = parse_timedtext_xml(xml)
    if not transcript:
        return ""

    return transcript


def fetch_transcript(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL. Expected watch/shorts/youtu.be link.")

    transcript = fetch_transcript_from_api(video_url=url, video_id=video_id)
    if transcript:
        return transcript

    transcript = fetch_transcript_with_fallback(video_url=url, video_id=video_id)
    if transcript:
        return transcript

    raise ValueError(
        "Transcript unavailable. Set YOUTUBE_TRANSCRIPT_API_TOKEN for youtube-transcript.io or use a public video with captions."
    )


def build_summary(url: str) -> SummaryResult:
    transcript = fetch_transcript(url)
    transcript_words = len(tokenize(transcript))

    short_min = 220
    short_max = min(1000, max(260, transcript_words // 4))
    long_min = 1000
    long_max = min(3000, max(1200, transcript_words // 2))

    short_summary = summarize_text(transcript, short_min, short_max)
    long_summary = summarize_text(transcript, long_min, long_max)

    if not short_summary:
        short_summary = transcript[:1200]
    if not long_summary:
        long_summary = transcript[:4000]

    return SummaryResult(
        transcript=transcript,
        short_summary=short_summary,
        long_summary=long_summary,
        short_read_minutes=minutes_for_words(len(tokenize(short_summary))),
        long_read_minutes=minutes_for_words(len(tokenize(long_summary))),
    )


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/summarize":
            self._send_json({"error": "Not found"}, status=404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            data = json.loads(raw)
            url = (data.get("url") or "").strip()
            if not url:
                self._send_json({"error": "Please provide a YouTube URL."}, status=400)
                return

            result = build_summary(url)
            self._send_json(
                {
                    "source_url": url,
                    "transcript": result.transcript,
                    "summary": {
                        "short": {
                            "text": result.short_summary,
                            "read_minutes": result.short_read_minutes,
                        },
                        "long": {
                            "text": result.long_summary,
                            "read_minutes": result.long_read_minutes,
                        },
                    },
                }
            )
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=422)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON payload."}, status=400)
        except Exception:
            self._send_json({"error": "Failed to summarize video. Try another URL."}, status=500)

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "4173"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    print(f"LazyTranscript running on http://localhost:{port}")
    server.serve_forever()
