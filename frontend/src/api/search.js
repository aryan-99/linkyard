const BASE = "http://localhost:8000";
async function request(path) {
    const res = await fetch(`${BASE}${path}`, {
        headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) {
        const detail = await res.text().catch(() => res.statusText);
        throw new Error(`${res.status}: ${detail}`);
    }
    return res.json();
}
export function searchLinks(q, limit = 20, offset = 0) {
    return request(`/links/search?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`);
}
