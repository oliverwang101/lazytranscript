const summarizeBtn = document.getElementById("summarizeBtn");
const videoUrlInput = document.getElementById("videoUrl");
const errorEl = document.getElementById("error");
const resultSection = document.getElementById("result");
const videoTitle = document.getElementById("videoTitle");

const tldrList = document.getElementById("tldr");
const insightsList = document.getElementById("insights");
const nextStepsList = document.getElementById("nextSteps");

const isYouTubeUrl = (url) => /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/.test(url);

const fillList = (el, items, ordered = false) => {
  el.innerHTML = "";
  items.forEach((item) => {
    const node = document.createElement("li");
    node.textContent = item;
    el.appendChild(node);
  });

  if (ordered && el.tagName !== "OL") {
    console.warn("Expected ordered list element");
  }
};

summarizeBtn.addEventListener("click", () => {
  const url = videoUrlInput.value.trim();

  if (!url) {
    errorEl.textContent = "Please paste a YouTube video URL.";
    resultSection.classList.add("hidden");
    return;
  }

  if (!isYouTubeUrl(url)) {
    errorEl.textContent = "This preview supports YouTube URLs only.";
    resultSection.classList.add("hidden");
    return;
  }

  errorEl.textContent = "";

  const preview = {
    title: "Sample summary (placeholder for API output)",
    tldr: [
      "This video explains the topic in three major sections with practical examples.",
      "The central takeaway is to use a repeatable framework instead of ad-hoc decisions.",
      "Most value comes from applying the method weekly, then iterating using feedback."
    ],
    insights: [
      "Start by identifying the single metric that defines success.",
      "Break long workflows into smaller checkpoints to reduce drop-off.",
      "Use lightweight templates to keep outputs consistent across content.",
      "Review outcomes with a short retrospective after each cycle."
    ],
    nextSteps: [
      "Write a one-page brief for your own version of the workflow.",
      "Apply the process to one 30-minute video this week.",
      "Track whether the summary saved at least 20 minutes.",
      "Refine prompt/output template based on what was unclear."
    ]
  };

  videoTitle.textContent = preview.title;
  fillList(tldrList, preview.tldr);
  fillList(insightsList, preview.insights);
  fillList(nextStepsList, preview.nextSteps, true);
  resultSection.classList.remove("hidden");
});
