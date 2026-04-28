const btn        = document.getElementById("save");
const status     = document.getElementById("status");
const pageTitle  = document.getElementById("page-title");
const pageUrl    = document.getElementById("page-url");
const optionsBtn = document.getElementById("options-btn");

// ── Options gear button ───────────────────────────────────────────────────────
optionsBtn.addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

// ── On load: populate title and URL from the active tab ──────────────────────
// chrome.tabs.query with "tabs" permission returns full tab.url and tab.title.
let currentTab = null;

(async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTab = tab ?? null;

  if (tab?.title) {
    pageTitle.textContent = tab.title;
  }
  if (tab?.url) {
    pageUrl.textContent = tab.url;
  }

  // Disable Save on any non-http(s) URL: internal browser pages, local files,
  // data URIs, and other extension pages cannot/should not be saved.
  const url = tab?.url ?? "";
  const isSaveable = url.startsWith("http://") || url.startsWith("https://");
  if (!isSaveable) {
    btn.disabled = true;
    status.className = "error";
    status.textContent = "Cannot save browser internal pages.";
  }
})();

// ── Save button ───────────────────────────────────────────────────────────────
btn.addEventListener("click", async () => {
  if (!currentTab) {
    status.className = "error";
    status.textContent = "No active tab found.";
    return;
  }

  btn.disabled = true;
  status.className = "saving";
  status.textContent = "Saving\u2026";

  const payload = {
    url: currentTab.url,
    title: currentTab.title ?? null,
  };

  // Route through the background service worker so the fetch runs in its
  // context (avoids popup-lifetime issues) and benefits from the configurable
  // API base URL stored in chrome.storage.sync.
  chrome.runtime.sendMessage({ type: "SAVE_LINK", payload }, (resp) => {
    if (chrome.runtime.lastError) {
      status.className = "error";
      status.textContent = "Extension error: " + chrome.runtime.lastError.message;
      btn.disabled = false;
      return;
    }

    if (resp?.ok) {
      btn.textContent = "Saved";
      btn.disabled = true;
      status.className = "success";
      status.textContent = "Saved!";
    } else {
      status.className = "error";
      status.textContent = "Failed: " + (resp?.status ?? resp?.error ?? "unknown error");
      btn.disabled = false;
    }
  });
});
