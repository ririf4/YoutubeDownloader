// noinspection DuplicatedCode

const urlInput = document.getElementById("urlInput");
const mediaType = document.getElementById("mediaType");
const resolutionSelect = document.getElementById("resolutionSelect");
const videoBitrateSelect = document.getElementById("videoBitrateSelect");
const audioBitrateSelect = document.getElementById("audioBitrateSelect");
const formatSelect = document.getElementById("formatSelect");
const outputDirInput = document.getElementById("outputDirInput");

const videoOptions = document.getElementById("videoOptions");
const audioOptions = document.getElementById("audioOptions");

const progressBar = document.getElementById("progressBar");
const statusText = document.getElementById("status");

document.getElementById("fetchOptions").addEventListener("click", fetchOptions);
document.getElementById("startDownload").addEventListener("click", startDownload);
document.getElementById("themeToggle").addEventListener("click", () => {
  document.body.classList.toggle("dark");
});
mediaType.addEventListener("change", updateUI);

updateUI();

function selectFolder() {
      if (window.pywebview) {
        window.pywebview.api.select_folder().then(folder => {
          if (folder) {
            document.getElementById('outputDirInput').value = folder;
          }
        });
      } else {
        alert("Folder picker only works in desktop app.");
      }
    }

function updateUI() {
  const type = mediaType.value;
  videoOptions.style.display = type === "video" ? "block" : "none";
  audioOptions.style.display = type === "audio" ? "block" : "none";

  if (window.lastOptions) {
    const formatList = type === "video"
      ? window.lastOptions.video.formats
      : window.lastOptions.audio.formats;

    formatSelect.innerHTML = formatList.map(f => `<option value="${f}">${f}</option>`).join("");
  }
}

async function fetchOptions() {
  const url = urlInput.value.trim();
  if (!url) return alert("Enter a valid YouTube URL");

  statusText.innerText = "Fetching options...";

  try {
    const res = await fetch("http://localhost:8000/options", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Server returned error:", res.status, errorText);
      statusText.innerText = `Error: ${res.status} - ${errorText}`;
      return;
    }

    const data = await res.json();
    console.log("Options response:", data);

    if (data.error) {
      statusText.innerText = "Error: " + data.error;
      return;
    }

    window.lastOptions = data;

    // --- Video Resolutions ---
    resolutionSelect.innerHTML = (data.video?.resolutions ?? []).flatMap(opt =>
      opt.source_formats.map(fmt =>
        `<option value="${opt.resolution}|${fmt}">${opt.resolution} [${fmt}]</option>`
      )
    ).join("");

    // --- Video Audio Bitrates ---
    videoBitrateSelect.innerHTML = (data.video?.audio_bitrates ?? []).flatMap(opt =>
      opt.source_formats.map(fmt =>
        `<option value="${opt.bitrate}|${fmt}">${opt.bitrate} [${fmt}]</option>`
      )
    ).join("");

    // --- Audio Bitrates ---
    audioBitrateSelect.innerHTML = (data.audio?.bitrates ?? []).flatMap(opt =>
      opt.source_formats.map(fmt =>
        `<option value="${opt.bitrate}|${fmt}">${opt.bitrate} [${fmt}]</option>`
      )
    ).join("");

    // --- Format List ---
    const formatList = mediaType.value === "video"
      ? data.video?.formats ?? []
      : data.audio?.formats ?? [];

    formatSelect.innerHTML = formatList.map(f =>
      `<option value="${f}">${f}</option>`
    ).join("");

    statusText.innerText = "Options loaded.";
  } catch (err) {
    console.error("Failed to fetch options:", err);
    statusText.innerText = "Error: Failed to fetch options. See console.";
  }

  const videoId = new URL(url).searchParams.get("v");
  if (videoId) {
    document.getElementById("thumbnail").src = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
    document.getElementById("previewFrame").src = `https://www.youtube.com/embed/${videoId}`;
    document.getElementById("previewSection").style.display = "block";
  }
}

async function startDownload() {
  const url = urlInput.value.trim();
  const type = mediaType.value;
  const outputDir = outputDirInput.value.trim();

  if (!url || !outputDir) {
    alert("URL and output folder are required.");
    return;
  }

  const resolutionFormat = (resolutionSelect.value || "").split("|");
  const videoBitrateFormat = (videoBitrateSelect.value || "").split("|");
  const audioBitrateFormat = (audioBitrateSelect.value || "").split("|");

  const payload = {
    url,
    type,
    format: formatSelect.value,
    resolution: type === "video" ? resolutionFormat[0] : null,
    resolution_format: type === "video" ? resolutionFormat[1] : null,
    audio_bitrate: type === "video"
        ? videoBitrateFormat[0]
        : audioBitrateFormat[0],
    audio_format: type === "video"
        ? videoBitrateFormat[1]
        : audioBitrateFormat[1],
    output_dir: outputDir
  };

  console.log("Download payload:", payload);

  progressBar.style.width = "0%";
  statusText.innerText = "Downloading...";

  // Optional: Fake progress while waiting
  let progress = 0;
  const interval = setInterval(() => {
    if (progress < 90) {
      progress += Math.random() * 5;
      progressBar.style.width = `${progress.toFixed(1)}%`;
    }
  }, 300);

  const res = await fetch("http://localhost:8000/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  clearInterval(interval);
  const result = await res.json();

  if (result.status === "success") {
    progressBar.style.width = "100%";
    statusText.innerText = "Download complete:\n" + result.file;
  } else {
    progressBar.style.width = "0%";
    statusText.innerText = "Error: " + result.message;
  }
}
