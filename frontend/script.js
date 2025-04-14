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

    // Populate video/audio options
    resolutionSelect.innerHTML = data.video.resolutions.map(r => `<option value="${r}">${r}</option>`).join("");
    videoBitrateSelect.innerHTML = data.video.audio_bitrates.map(b => `<option value="${b}">${b}</option>`).join("");
    audioBitrateSelect.innerHTML = data.audio.bitrates.map(b => `<option value="${b}">${b}</option>`).join("");

    const formatList = mediaType.value === "video" ? data.video.formats : data.audio.formats;
    formatSelect.innerHTML = formatList.map(f => `<option value="${f}">${f}</option>`).join("");

    statusText.innerText = "Options loaded.";
  } catch (err) {
    console.error("Failed to fetch options:", err);
    statusText.innerText = "Error: Failed to fetch options. See console.";
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

  const payload = {
    url,
    type,
    format: formatSelect.value,
    resolution: type === "video" ? resolutionSelect.value : null,
    video_bitrate: type === "video" ? videoBitrateSelect.value : null,
    audio_bitrate: type === "audio" ? audioBitrateSelect.value : null,
    output_dir: outputDir
  };

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
