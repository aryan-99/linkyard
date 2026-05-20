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

  if (!raw) {
    showStatus("error", "URL cannot be empty.");
    return;
  }

  var parsed;
  try {
    parsed = new URL(raw);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      showStatus("error", "URL must start with http:// or https://.");
      return;
    }
  } catch (_) {
    showStatus("error", "Not a valid URL.");
    return;
  }

  // Strip trailing slash silently
  var value = raw.replace(/\/+$/, "");

  var isLocalhost = parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1";

  if (isLocalhost) {
    persistApiBase(value);
  } else {
    // Remote hosts require an explicit permission grant so the extension can
    // reach any user-configured backend (optional_host_permissions in manifest).
    chrome.permissions.request({ origins: [parsed.origin + "/*"] }, function(granted) {
      if (!granted) {
        showStatus("error", "Permission denied. Please allow access to save this URL.");
        return;
      }
      persistApiBase(value);
    });
  }
});

function persistApiBase(value) {
  chrome.storage.sync.set({ apiBase: value }, function() {
    if (chrome.runtime.lastError) {
      showStatus("error", "Save failed: " + chrome.runtime.lastError.message);
      return;
    }
    input.value = value;
    showStatus("success", "Saved.");
  });
}

function showStatus(type, message) {
  status.className = type;
  status.textContent = message;
}
