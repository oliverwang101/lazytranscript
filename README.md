# LazyTranscript

LazyTranscript turns YouTube videos into readable summaries so you can learn faster without watching every minute.

## What this version does

- Accepts a real YouTube URL
- Pulls the video's transcript (when captions are available)
- Generates:
  - **Short summary** (~1–5 minute read)
  - **Long summary** (~5–15 minute read)
- Shows the full transcript in the UI for transparency

## Quickstart (repo root)

### 1) Configure transcript API token (recommended)

```bash
export YOUTUBE_TRANSCRIPT_API_TOKEN="<your-youtube-transcript-io-token>"
```

On Windows PowerShell:

```powershell
$env:YOUTUBE_TRANSCRIPT_API_TOKEN="<your-youtube-transcript-io-token>"
```

### 2) Start the web app + API server

```bash
python3 app.py
```

Or use helper scripts:

```bash
./run.sh
```

```powershell
.\run.ps1
```

### 3) Open the app

Open `http://localhost:4173`.

> Important: `python3 -m http.server --directory web` only serves static files and **will not** generate transcripts.
> Use `python3 app.py` (or `py app.py`) so the `/api/summarize` backend is available.

## Windows notes

If `python3` is not recognized, use:

```powershell
py app.py
```

If `py` is also not available, install Python from https://python.org and re-run the commands above.

## How the summarization works (current implementation)

1. Extract YouTube video ID from the URL.
2. Fetch transcript using `https://www.youtube-transcript.io/api` when `YOUTUBE_TRANSCRIPT_API_TOKEN` is set.
3. Fallback to direct YouTube caption track extraction if API retrieval is unavailable.
4. Score transcript sentences using term frequency + position/length weighting.
5. Build two extractive summaries with different target lengths.

This is a practical baseline. You can later swap in an LLM summarizer while keeping the same API contract.

## API contract

### `POST /api/summarize`

Request:

```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

Response:

```json
{
  "source_url": "https://www.youtube.com/watch?v=...",
  "transcript": "...",
  "summary": {
    "short": {
      "text": "...",
      "read_minutes": 3
    },
    "long": {
      "text": "...",
      "read_minutes": 8
    }
  }
}
```

## Known limitations

- Currently supports YouTube URLs only.
- Requires transcript availability either through youtube-transcript.io API token or YouTube public captions.
- Summaries are extractive (sentence selection), not generative/abstractive.

## Next steps

- Add optional LLM abstractive summarization for better readability.
- Add chapter-level timestamp mapping.
- Add saved history per user.
- Add support for non-YouTube sources.
