const btn = document.getElementById("save");
const status = document.getElementById("status");

btn.addEventListener("click", async () => {
  status.textContent = "Saving...";
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    status.textContent = "No active tab.";
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
    status.textContent = resp?.ok ? "Saved" : `Failed (${resp?.status ?? resp?.error ?? "?"})`;
  });
});
