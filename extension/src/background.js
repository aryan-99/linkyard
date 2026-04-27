const DEFAULT_API_BASE = "http://localhost:8000";

async function getApiBase() {
  const { apiBase } = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE });
  return apiBase;
}

// Sender origin check: chrome.runtime.onMessage only receives messages from
// the same extension (popup, content scripts) — external websites cannot reach
// this listener. No additional sender.id check is required for same-extension
// messaging, but any future content-script → background path MUST validate
// sender.tab.url before trusting tab-derived data.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type !== "SAVE_LINK") return;
  (async () => {
    try {
      const base = await getApiBase();
      const res = await fetch(`${base}/links`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...msg.payload, source: "extension" }),
      });
      sendResponse({ ok: res.ok, status: res.status });
    } catch (err) {
      sendResponse({ ok: false, error: String(err) });
    }
  })();
  return true;
});
