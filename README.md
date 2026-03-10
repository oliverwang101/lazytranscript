# LazyTranscript

LazyTranscript is a video-to-reading application that helps people consume long-form video content in a fraction of the time.

## Initial web app (now available)

You can run a lightweight starter web app locally right now:

```bash
python3 -m http.server 4173 --directory web
```

Then open: `http://localhost:4173`

### If Python is not installed (common on Windows)

Use one of these options from repo root:

1. Try the Windows Python launcher:
```powershell
py -m http.server 4173 --directory web
```

2. Open the static app directly (no server required for this prototype):
```powershell
start .\web\index.html
```

What this starter includes:
- YouTube URL input field
- Basic client-side URL validation
- Mock summary output section (TL;DR, Top Insights, Next Steps)

> Note: this is a front-end preview so far; it does not call a real transcription/summarization backend yet.

## Product vision

Turn a 30-minute video into:
- a **5–10 minute readable brief**,
- a **1–2 minute quick skim**, and
- **actionable next steps** tailored to the viewer.

The first version focuses on YouTube URLs, then evolves into a homepage overlay experience that transforms a user's YouTube feed into a personalized "news desk" of readable summaries.

## Core user stories

1. **As a viewer**, I can paste a YouTube link and get a high-quality summary without watching the entire video.
2. **As a power user**, I can choose summary depth (quick skim vs deep brief).
3. **As a learner/professional**, I can get recommended next actions based on the video's content.
4. **As a YouTube-heavy user**, I can connect my YouTube account and view summaries for my feed.

## MVP scope (Phase 1)

### In scope
- Input: public YouTube URL.
- Pipeline:
  1. Fetch metadata and transcript (official captions first; fallback to speech-to-text).
  2. Chunk transcript and generate multi-level summaries.
  3. Generate key takeaways, timestamps, and recommendations.
- Output UI:
  - **Quick Read** (1–2 min)
  - **Standard Read** (5–10 min)
  - **Key Points + Next Steps**
- Basic account system to store history.

### Out of scope (for MVP)
- Browser extension overlay for the YouTube homepage.
- Full social sharing layer.
- Multi-language translation pipeline.

## Output format curation (recommended)

Each video summary should be produced in a consistent format:

1. **TL;DR (3 bullets max)**
2. **What this video is about (short paragraph)**
3. **Top insights (5–8 bullets)**
4. **Actionable next steps (3–5 items)**
5. **Who this is for / who should skip**
6. **Confidence + caveats** (e.g., missing transcript sections)
7. **Optional timestamp map** for users who want to jump into the original video

### Two-length strategy

- **Quick Skim**: ~150–250 words, optimized for fast decision-making.
- **Deep Brief**: ~700–1,200 words, optimized for understanding and retention.

## Recommended system architecture

### Ingestion layer
- Accept URL input.
- Normalize and validate source.
- Pull metadata (title, channel, duration, publish date).

### Transcript layer
- Source priority:
  1. Platform captions
  2. Existing transcript providers
  3. ASR fallback for audio extraction
- Store transcript with timestamps and speaker segments when available.

### Understanding layer
- Chunk long transcripts by semantic boundaries + token limits.
- Generate per-chunk summaries.
- Merge into hierarchical final summary:
  - chunk summary -> section summary -> final summary

### Recommendation layer
- Extract intent from the video (learn, buy, implement, compare, etc.).
- Produce tailored next-step suggestions.
- Attach links/resources where possible.

### Delivery layer
- Web app with cards representing summarized videos.
- Reading-time indicator and summary-depth toggle.
- Save/bookmark/history.

## Scale considerations

- Use asynchronous jobs for transcription/summarization.
- Queue-based architecture (e.g., ingestion queue, transcript queue, summarization queue).
- Cache transcripts and summaries by canonical video ID.
- Add retries + dead-letter queue for failed jobs.
- Track quality metrics:
  - transcript coverage,
  - summary latency,
  - user ratings on usefulness.

## Suggested phased roadmap

### Phase 1 (0 -> 1): YouTube link summarizer
- URL input -> transcript -> two summary lengths -> next steps.
- User history and saved items.

### Phase 2 (1 -> N): Personalization
- Connect YouTube account.
- Summarize subscriptions/home feed videos.
- Rank summaries by user interests.

### Phase 3: Overlay + workflow integration
- Browser extension overlay for YouTube homepage.
- "Replace thumbnails with readable briefs" mode.
- Integrations with note-taking apps.

## API design (starter)

### `POST /api/videos/summarize`
Request:
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "depth": "quick|deep",
  "include_recommendations": true
}
```

Response:
```json
{
  "video": {
    "id": "...",
    "title": "...",
    "duration_seconds": 1800
  },
  "summary": {
    "quick": "...",
    "deep": "...",
    "key_points": ["..."],
    "next_steps": ["..."],
    "caveats": ["..."]
  },
  "status": "completed"
}
```

## Quality rubric for summaries

Use this rubric to review output quality:
- **Accuracy**: faithful to source content.
- **Compression quality**: key points preserved despite shorter length.
- **Actionability**: clear recommendations and next steps.
- **Readability**: easy to skim and structured.
- **Trust**: clear caveats when confidence is low.

## What you can help curate next

To tighten output quality quickly, define:
1. Your preferred tone (journalistic, analytical, casual).
2. Your preferred summary templates by content type (news, podcasts, tutorials, interviews).
3. How opinionated recommendations should be (conservative vs assertive).
4. Minimum quality threshold before a summary is shown.

Once these are decided, they can be converted into prompt templates and evaluation tests for consistent output at scale.
