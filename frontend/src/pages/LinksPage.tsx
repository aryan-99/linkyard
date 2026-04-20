import { useEffect, useState } from "react";
import AddLinkForm from "../components/AddLinkForm";
import { deleteLink, listLinks, type LinkDetailResponse, type LinkResponse } from "../api/links";

const PAGE_SIZE = 20;

export default function LinksPage() {
  const [items, setItems] = useState<LinkResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function fetchLinks(currentOffset: number, append: boolean) {
    try {
      const data = await listLinks(PAGE_SIZE, currentOffset);
      setTotal(data.pagination.total);
      setItems((prev) => (append ? [...prev, ...data.items] : data.items));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load links");
    }
  }

  useEffect(() => {
    setLoading(true);
    fetchLinks(0, false).finally(() => setLoading(false));
  }, []);

  async function handleRefresh() {
    setRefreshing(true);
    setOffset(0);
    await fetchLinks(0, false);
    setRefreshing(false);
  }

  async function handleLoadMore() {
    const nextOffset = offset + PAGE_SIZE;
    setLoadingMore(true);
    await fetchLinks(nextOffset, true);
    setOffset(nextOffset);
    setLoadingMore(false);
  }

  function handleCreated(link: LinkDetailResponse) {
    setItems((prev) => [link, ...prev]);
    setTotal((t) => t + 1);
  }

  async function handleDelete(id: string) {
    try {
      await deleteLink(id);
      setItems((prev) => prev.filter((l) => l.id !== id));
      setTotal((t) => t - 1);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete link");
    }
  }

  return (
    <div style={styles.page}>
      <AddLinkForm onCreated={handleCreated} />

      <section>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionHeading}>
            Saved links{total > 0 && <span style={styles.count}> ({total})</span>}
          </h2>
          <button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            style={styles.refreshBtn}
            title="Refresh"
            aria-label="Refresh links"
          >
            {refreshing ? "↻" : "↻"}
          </button>
        </div>

        {loading && <p style={styles.muted}>Loading…</p>}
        {error && <p style={styles.error}>{error}</p>}

        {!loading && items.length === 0 && (
          <p style={styles.muted}>No links saved yet. Add one above.</p>
        )}

        <ul style={styles.list}>
          {items.map((link) => (
            <LinkRow key={link.id} link={link} onDelete={handleDelete} />
          ))}
        </ul>

        {items.length < total && (
          <button
            onClick={handleLoadMore}
            disabled={loadingMore}
            style={styles.loadMore}
          >
            {loadingMore ? "Loading…" : "Load more"}
          </button>
        )}
      </section>
    </div>
  );
}

/* ─── LinkRow sub-component (handles its own hover state) ─────────────────── */

interface LinkRowProps {
  link: LinkResponse;
  onDelete: (id: string) => void;
}

function LinkRow({ link, onDelete }: LinkRowProps) {
  const [hovered, setHovered] = useState(false);

  const itemStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    padding: "12px 8px",
    borderBottom: "1px solid var(--color-border)",
    borderRadius: 4,
    background: hovered ? "var(--color-hover-bg)" : "transparent",
    transition: "background 0.12s",
  };

  const deleteBtnStyle: React.CSSProperties = {
    flexShrink: 0,
    background: "none",
    border: "none",
    color: hovered ? "var(--color-error)" : "transparent",
    cursor: "pointer",
    fontSize: 14,
    padding: "2px 4px",
    transition: "color 0.12s",
    lineHeight: 1,
  };

  return (
    <li
      style={itemStyle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={styles.itemMain}>
        <a
          href={link.url}
          target="_blank"
          rel="noopener noreferrer"
          style={styles.itemTitle}
        >
          {link.title ?? link.url}
        </a>
        {link.title && (
          <span style={styles.itemUrl}>{link.url}</span>
        )}
        {link.snippet && (
          <p style={styles.itemSnippet}>{link.snippet}</p>
        )}
        <span style={styles.itemMeta}>
          {new Date(link.created_at).toLocaleDateString()} · {link.source}
        </span>
      </div>
      <button
        onClick={() => onDelete(link.id)}
        style={deleteBtnStyle}
        title="Delete"
        aria-label="Delete link"
        tabIndex={hovered ? 0 : -1}
      >
        ✕
      </button>
    </li>
  );
}

/* ─── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: 680,
    margin: "0 auto",
    padding: "32px 16px",
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  sectionHeading: {
    fontSize: 15,
    fontWeight: 600,
    margin: 0,
    color: "var(--color-text-primary)",
  },
  refreshBtn: {
    background: "none",
    border: "none",
    color: "var(--color-text-muted)",
    cursor: "pointer",
    fontSize: 18,
    lineHeight: 1,
    padding: "2px 4px",
    borderRadius: 4,
  },
  count: {
    fontWeight: 400,
    color: "var(--color-text-muted)",
  },
  muted: { color: "var(--color-text-muted)", fontSize: 14 },
  error: { color: "var(--color-error)", fontSize: 14 },
  list: { listStyle: "none", padding: 0, margin: 0 },
  itemMain: { flex: 1, minWidth: 0 },
  itemTitle: {
    display: "block",
    fontWeight: 500,
    fontSize: 15,
    color: "var(--color-text-primary)",
    textDecoration: "none",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  itemUrl: {
    display: "block",
    fontSize: 12,
    color: "var(--color-text-muted)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    marginTop: 2,
  },
  itemSnippet: {
    margin: "4px 0 0",
    fontSize: 13,
    color: "var(--color-text-secondary)",
  },
  itemMeta: {
    fontSize: 11,
    color: "var(--color-text-muted)",
    marginTop: 4,
    display: "block",
  },
  loadMore: {
    marginTop: 16,
    padding: "8px 20px",
    background: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: 4,
    fontSize: 14,
    cursor: "pointer",
    color: "var(--color-text-secondary)",
  },
};
