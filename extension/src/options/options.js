var DEFAULT_API_BASE = "http://localhost:8000";

var input  = document.getElementById("api-base");
var btn    = document.getElementById("save");
var status = document.getElementById("status");

// ── On load: read stored value and populate the input ────────────────────────
chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE }, function(items) {
  input.value = items.apiBase;
});

// ── Save button ───────────────────────────────────────────────────────────────
btn.addEventListener("click", function() {
  var raw = input.value.trim();

  // Reject empty values
  if (!raw) {
    showStatus("error", "URL cannot be empty.");
    return;
  }

  // Must start with http:// or https://
  if (!raw.startsWith("http://") && !raw.startsWith("https://")) {
    showStatus("error", "URL must start with http:// or https://.");
    return;
  }

  // Validate as a URL
  try {
    new URL(raw);
  } catch (_) {
    showStatus("error", "Not a valid URL.");
    return;
  }

  // Strip trailing slash silently
  var value = raw.replace(/\/+$/, "");

  chrome.storage.sync.set({ apiBase: value }, function() {
    if (chrome.runtime.lastError) {
      showStatus("error", "Save failed: " + chrome.runtime.lastError.message);
      return;
    }
    input.value = value;
    showStatus("success", "Saved.");
  });
});

function showStatus(type, message) {
  status.className = type;
  status.textContent = message;
}
