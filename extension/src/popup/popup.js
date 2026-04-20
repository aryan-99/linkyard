const btn        = document.getElementById("save");
const status     = document.getElementById("status");
const pageTitle  = document.getElementById("page-title");

// ── On load: show the active tab's title in the header area ──────────────────
(async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.title) {
    pageTitle.textContent = tab.title;
  }
})();

// ── Save button ──────────────────────────────────────────────────────────────
btn.addEventListener("click", async () => {
  status.className = "saving";
  status.textContent = "Saving\u2026";
  btn.disabled = true;

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    status.className = "error";
    status.textContent = "No active tab.";
    btn.disabled = false;
    return;
  }

  const [{ result } = {}] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => ({
      url: location.href,
      title: document.title,
      meta_description:
        document.querySelector('meta[name="description"]')?.content ??
        document.querySelector('meta[property="og:description"]')?.content ??
        null,
    }),
  });

  chrome.runtime.sendMessage({ type: "SAVE_LINK", payload: result }, (resp) => {
    if (resp?.ok) {
      btn.textContent = "Saved";
      btn.disabled = true;
      status.className = "";
      status.textContent = "";
    } else {
      status.className = "error";
      status.textContent = `Failed (${resp?.status ?? resp?.error ?? "?"})`;
      btn.disabled = false;
    }
  });
});
