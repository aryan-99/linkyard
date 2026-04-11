function readMeta(name) {
  const el = document.querySelector(`meta[name="${name}"]`) || document.querySelector(`meta[property="og:${name}"]`);
  return el?.getAttribute("content") ?? null;
}

window.__linkyardScrape = () => ({
  url: location.href,
  title: document.title,
  meta_description: readMeta("description"),
});
