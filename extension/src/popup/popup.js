const btn        = document.getElementById("save");
const status     = document.getElementById("status");
const pageTitle  = document.getElementById("page-title");
const pageUrl    = document.getElementById("page-url");
const optionsBtn = document.getElementById("options-btn");
const snippetEl  = document.getElementById("snippet");

function showStatus(type, message) {
  status.className = type;
  status.textContent = message;
}

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
    showStatus("error", "Cannot save browser internal pages.");
  }
})();

// ── Save button ───────────────────────────────────────────────────────────────
btn.addEventListener("click", async () => {
  if (!currentTab) {
    showStatus("error", "No active tab found.");
    return;
  }

  btn.disabled = true;
  snippetEl.disabled = true;
  showStatus("saving", "Saving\u2026");

  const snippet = snippetEl.value.trim();
  const payload = {
    url: currentTab.url,
    title: currentTab.title ?? null,
    ...(snippet ? { snippet } : {}),
  };

  // Route through the background service worker so the fetch runs in its
  // context (avoids popup-lifetime issues) and benefits from the configurable
  // API base URL stored in chrome.storage.sync.
  chrome.runtime.sendMessage({ type: "SAVE_LINK", payload }, (resp) => {
    if (chrome.runtime.lastError) {
      showStatus("error", "Extension error: " + chrome.runtime.lastError.message);
      btn.disabled = false;
      snippetEl.disabled = false;
      return;
    }

    if (resp?.ok) {
      btn.textContent = "Saved";
      btn.disabled = true;
      showStatus("success", "Saved!");
    } else {
      showStatus("error", "Failed: " + (resp?.status ?? resp?.error ?? "unknown error"));
      btn.disabled = false;
      snippetEl.disabled = false;
    }
  });
});
