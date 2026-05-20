import { useEffect, useRef, useState } from "react";
import { SearchResultItem, SearchResultsResponse, searchLinks } from "../api/search";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query.trim()) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const data: SearchResultsResponse = await searchLinks(query.trim());
        setResults(data.items);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search failed");
      } finally {
        setLoading(false);
      }
    }, 300);
  }, [query]);

  return (
    <div style={styles.page}>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search your links…"
        style={styles.searchInput}
        autoFocus
      />

      {loading && <p style={styles.muted}>Searching…</p>}
      {error && <p style={styles.error}>{error}</p>}

      {!loading && query.trim() && results.length === 0 && !error && (
        <p style={styles.muted}>No results for "{query}"</p>
      )}

      <ul style={styles.list}>
        {results.map((item) => (
          <SearchRow key={item.id} item={item} />
        ))}
      </ul>
    </div>
  );
}

/* ─── SearchRow sub-component ─────────────────────────────────────────────── */

interface SearchRowProps {
  item: SearchResultItem;
}

function SearchRow({ item }: SearchRowProps) {
  const [hovered, setHovered] = useState(false);

  const rowStyle: React.CSSProperties = {
    padding: "12px 8px",
    borderBottom: "1px solid var(--color-border)",
    borderRadius: 4,
    background: hovered ? "var(--color-hover-bg)" : "transparent",
    transition: "background 0.12s",
  };

  return (
    <li
      style={rowStyle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={styles.rowHeader}>
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          style={styles.itemTitle}
        >
          {item.title ?? item.url}
        </a>
        <span style={styles.scoreBadge} title="Semantic similarity score">
          {Math.max(0, Math.round(item.score * 100))}% match
        </span>
      </div>
      <div style={styles.itemUrl}>{item.url}</div>
      {item.snippet && (
        <div style={styles.itemSnippet}>{item.snippet}</div>
      )}
    </li>
  );
}

/* ─── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: 720,
    margin: "0 auto",
    padding: "32px 16px",
  },
  searchInput: {
    width: "100%",
    padding: "10px 12px",
    fontSize: 15,
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    background: "var(--color-surface)",
    color: "var(--color-text-primary)",
    fontFamily: "inherit",
    marginBottom: 16,
  },
  muted: { color: "var(--color-text-muted)", fontSize: 14 },
  error: { color: "var(--color-error)", fontSize: 14 },
  list: { listStyle: "none", padding: 0, margin: 0 },
  rowHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "baseline",
    gap: 8,
  },
  itemTitle: {
    fontWeight: 600,
    fontSize: 15,
    color: "var(--color-accent)",
    textDecoration: "none",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    minWidth: 0,
    flex: 1,
  },
  scoreBadge: {
    flexShrink: 0,
    fontSize: 11,
    fontWeight: 500,
    color: "var(--color-accent)",
    background: "var(--color-accent-tint)",
    border: "1px solid var(--color-accent)",
    borderRadius: 4,
    padding: "1px 6px",
    whiteSpace: "nowrap",
    opacity: 0.9,
  },
  itemUrl: {
    fontSize: 12,
    color: "var(--color-text-muted)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    marginTop: 2,
  },
  itemSnippet: {
    marginTop: 4,
    fontSize: 13,
    color: "var(--color-text-secondary)",
  },
};
