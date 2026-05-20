import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useRef, useState } from "react";
import { searchLinks } from "../api/search";
export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const debounceRef = useRef(null);
    useEffect(() => {
        if (debounceRef.current)
            clearTimeout(debounceRef.current);
        if (!query.trim()) {
            setResults([]);
            setLoading(false);
            return;
        }
        setLoading(true);
        debounceRef.current = setTimeout(async () => {
            try {
                const data = await searchLinks(query.trim());
                setResults(data.items);
                setError(null);
            }
            catch (e) {
                setError(e instanceof Error ? e.message : "Search failed");
            }
            finally {
                setLoading(false);
            }
        }, 300);
    }, [query]);
    return (_jsxs("div", { style: styles.page, children: [_jsx("input", { type: "search", value: query, onChange: (e) => setQuery(e.target.value), placeholder: "Search your links\u2026", style: styles.searchInput, autoFocus: true }), loading && _jsx("p", { style: styles.muted, children: "Searching\u2026" }), error && _jsx("p", { style: styles.error, children: error }), !loading && query.trim() && results.length === 0 && !error && (_jsxs("p", { style: styles.muted, children: ["No results for \"", query, "\""] })), _jsx("ul", { style: styles.list, children: results.map((item) => (_jsx(SearchRow, { item: item }, item.id))) })] }));
}
function SearchRow({ item }) {
    const [hovered, setHovered] = useState(false);
    const rowStyle = {
        padding: "12px 8px",
        borderBottom: "1px solid var(--color-border)",
        borderRadius: 4,
        background: hovered ? "var(--color-hover-bg)" : "transparent",
        transition: "background 0.12s",
    };
    return (_jsxs("li", { style: rowStyle, onMouseEnter: () => setHovered(true), onMouseLeave: () => setHovered(false), children: [_jsxs("div", { style: styles.rowHeader, children: [_jsx("a", { href: item.url, target: "_blank", rel: "noopener noreferrer", style: styles.itemTitle, children: item.title ?? item.url }), _jsxs("span", { style: styles.scoreBadge, title: "Semantic similarity score", children: [Math.max(0, Math.round(item.score * 100)), "% match"] })] }), _jsx("div", { style: styles.itemUrl, children: item.url }), item.snippet && (_jsx("div", { style: styles.itemSnippet, children: item.snippet }))] }));
}
/* ─── Styles ──────────────────────────────────────────────────────────────── */
const styles = {
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
