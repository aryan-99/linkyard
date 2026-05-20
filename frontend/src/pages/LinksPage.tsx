import { useEffect, useState } from "react";
import AddLinkForm from "../components/AddLinkForm";
import {
  deleteLink,
  listLinks,
  refetchLink,
  type LinkDetailResponse,
  type LinkResponse,
} from "../api/links";

const PAGE_SIZE = 20;

export default function LinksPage() {
  const [items, setItems] = useState<LinkResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshHovered, setRefreshHovered] = useState(false);

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

  function handleRefetched(updated: LinkDetailResponse) {
    setItems((prev) => prev.map((l) => (l.id === updated.id ? updated : l)));
  }

  return (
    <div style={styles.page}>
      <AddLinkForm onCreated={handleCreated} />

      <section>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionHeading}>
            Saved links{total > 0 && <span style={styles.count}> ({total})</span>}
          </h2>
          <span
            style={styles.tooltipWrap}
            onMouseEnter={() => setRefreshHovered(true)}
            onMouseLeave={() => setRefreshHovered(false)}
          >
            <button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              style={styles.refreshBtn}
              aria-label="Refresh links"
            >
              {refreshing ? "↻" : "↻"}
            </button>
            {refreshHovered && !refreshing && (
              <span style={styles.tooltip}>Refresh</span>
            )}
          </span>
        </div>

        {loading && <p style={styles.muted}>Loading…</p>}
        {error && <p style={styles.error}>{error}</p>}

        {!loading && items.length === 0 && (
          <p style={styles.muted}>No links saved yet. Add one above.</p>
        )}

        <ul style={styles.list}>
          {items.map((link) => (
            <LinkRow
              key={link.id}
              link={link}
              onDelete={handleDelete}
              onRefetched={handleRefetched}
            />
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
  onRefetched: (updated: LinkDetailResponse) => void;
}

function LinkRow({ link, onDelete, onRefetched }: LinkRowProps) {
  const [hovered, setHovered] = useState(false);
  const [btnHovered, setBtnHovered] = useState(false);
  const [deleteHovered, setDeleteHovered] = useState(false);
  const [refetching, setRefetching] = useState(false);
  const [refetchDone, setRefetchDone] = useState(false);

  async function handleRefetch() {
    if (refetching) return;
    setRefetching(true);
    setRefetchDone(false);
    try {
      const updated = await refetchLink(link.id);
      onRefetched(updated);
      setRefetchDone(true);
      setTimeout(() => setRefetchDone(false), 2000);
    } catch {
      // silently ignore — could add error state here if desired
    } finally {
      setRefetching(false);
    }
  }

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

  const refetchBtnStyle: React.CSSProperties = {
    flexShrink: 0,
    background: "none",
    border: "none",
    color: hovered
      ? refetchDone
        ? "var(--color-success)"
        : "var(--color-text-muted)"
      : "transparent",
    cursor: refetching ? "not-allowed" : "pointer",
    fontSize: 14,
    padding: "2px 4px",
    transition: "color 0.12s",
    lineHeight: 1,
    opacity: refetching ? 0.5 : 1,
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
          <p style={styles.itemSnippet}>
            <span style={styles.itemFieldLabel}>Note: </span>{link.snippet}
          </p>
        )}
        {link.page_body_preview && (
          <p style={styles.itemBodyPreview}>
            <span style={styles.itemFieldLabel}>Extracted: </span>{link.page_body_preview}
          </p>
        )}
        <span style={styles.itemMeta}>
          {new Date(link.created_at).toLocaleDateString()} · {link.source}
        </span>
      </div>

      {/* Re-fetch button */}
      <span
        style={styles.tooltipWrap}
        onMouseEnter={() => setBtnHovered(true)}
        onMouseLeave={() => setBtnHovered(false)}
      >
        <button
          onClick={handleRefetch}
          disabled={refetching}
          style={refetchBtnStyle}
          title="Re-fetch page content"
          aria-label="Re-fetch page content"
          tabIndex={hovered ? 0 : -1}
        >
          {refetchDone ? "✓" : "⟳"}
        </button>
        {btnHovered && !refetching && !refetchDone && (
          <span style={styles.tooltip}>Re-fetch page content</span>
        )}
      </span>

      {/* Delete button */}
      <span
        style={styles.tooltipWrap}
        onMouseEnter={() => setDeleteHovered(true)}
        onMouseLeave={() => setDeleteHovered(false)}
      >
        <button
          onClick={() => onDelete(link.id)}
          style={deleteBtnStyle}
          aria-label="Delete link"
          tabIndex={hovered ? 0 : -1}
        >
          ✕
        </button>
        {deleteHovered && (
          <span style={styles.tooltip}>Delete</span>
        )}
      </span>
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
    color: "var(--color-accent)",
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
  itemFieldLabel: {
    fontSize: 11,
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.04em",
    color: "var(--color-text-muted)",
    marginRight: 2,
  },
  itemSnippet: {
    margin: "4px 0 0",
    fontSize: 13,
    color: "var(--color-text-secondary)",
  },
  itemBodyPreview: {
    margin: "4px 0 0",
    fontSize: 12,
    color: "var(--color-text-muted)",
    overflow: "hidden",
    display: "-webkit-box",
    // reason: non-standard CSS property required for line-clamp
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    lineHeight: 1.4,
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
  tooltipWrap: {
    position: "relative",
    flexShrink: 0,
    display: "inline-flex",
    alignItems: "center",
  },
  tooltip: {
    position: "absolute",
    bottom: "calc(100% + 4px)",
    right: 0,
    background: "var(--color-text-primary)",
    color: "var(--color-bg)",
    fontSize: 11,
    padding: "3px 7px",
    borderRadius: 4,
    whiteSpace: "nowrap",
    pointerEvents: "none",
    zIndex: 10,
  },
};
