const summarizeBtn = document.getElementById("summarizeBtn");
const videoUrlInput = document.getElementById("videoUrl");
const errorEl = document.getElementById("error");
const resultSection = document.getElementById("result");

const shortSummaryEl = document.getElementById("shortSummary");
const longSummaryEl = document.getElementById("longSummary");
const transcriptEl = document.getElementById("transcript");
const shortReadTimeEl = document.getElementById("shortReadTime");
const longReadTimeEl = document.getElementById("longReadTime");

const isYouTubeUrl = (url) => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/.test(url);

const setLoading = (loading) => {
  summarizeBtn.disabled = loading;
  summarizeBtn.textContent = loading ? "Summarizing..." : "Summarize";
};

const renderResult = (payload) => {
  shortSummaryEl.textContent = payload.summary.short.text;
  longSummaryEl.textContent = payload.summary.long.text;
  transcriptEl.textContent = payload.transcript;
  shortReadTimeEl.textContent = `~${payload.summary.short.read_minutes} min read`;
  longReadTimeEl.textContent = `~${payload.summary.long.read_minutes} min read`;
  resultSection.classList.remove("hidden");
};

summarizeBtn.addEventListener("click", async () => {
  const url = videoUrlInput.value.trim();
  resultSection.classList.add("hidden");

  if (!url) {
    errorEl.textContent = "Please paste a YouTube video URL.";
    return;
  }

  if (!isYouTubeUrl(url)) {
    errorEl.textContent = "This app currently supports YouTube URLs only.";
    return;
  }

  errorEl.textContent = "";
  setLoading(true);

  try {
    const response = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch (_parseError) {
      data = {};
    }

    if (!response.ok) {
      if (response.status === 404 || response.status === 405 || response.status === 501) {
        throw new Error(
          "Backend API not found. Start the app with `python3 app.py` (or `py app.py`) instead of a static server command."
        );
      }
      throw new Error(data.error || "Failed to summarize video.");
    }

    if (!data.summary || !data.transcript) {
      throw new Error("Backend response was invalid. Please restart the API server and try again.");
    }

    renderResult(data);
  } catch (error) {
    errorEl.textContent = error.message || "An unexpected error occurred.";
  } finally {
    setLoading(false);
  }
});
