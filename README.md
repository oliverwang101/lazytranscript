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

### 1) Start the web app + API server

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

### 2) Open the app

Open `http://localhost:4173`.

## Windows notes

If `python3` is not recognized, use:

```powershell
py app.py
```

If `py` is also not available, install Python from https://python.org and re-run the commands above.

## How the summarization works (current implementation)

1. Extract YouTube video ID from the URL.
2. Download transcript from YouTube caption tracks using the built-in HTTP client.
3. Score transcript sentences using term frequency + position/length weighting.
4. Build two extractive summaries with different target lengths.

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
- Requires a transcript/captions to be available for the selected video.
- Summaries are extractive (sentence selection), not generative/abstractive.

## Next steps

- Add optional LLM abstractive summarization for better readability.
- Add chapter-level timestamp mapping.
- Add saved history per user.
- Add support for non-YouTube sources.
