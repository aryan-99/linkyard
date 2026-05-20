import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/* ─── Footer ─────────────────────────────────────────────────────────────────
   Persistent site-wide footer. Rendered once in App.tsx.
   GitHub SVG is inlined so there is no dependency on any icon library.
──────────────────────────────────────────────────────────────────────────── */
export function Footer() {
    return (_jsxs("footer", { style: styles.footer, children: [_jsx("span", { style: styles.credit, children: "Built by Aryan Mittal" }), _jsxs("a", { href: "https://github.com/aryan-99/linkyard", target: "_blank", rel: "noopener noreferrer", style: styles.githubLink, "aria-label": "Linkyard on GitHub", children: [_jsx(GitHubIcon, {}), _jsx("span", { style: styles.githubLabel, children: "GitHub" })] })] }));
}
/* ─── GitHub mark SVG (official simplified path, monochrome) ────────────── */
function GitHubIcon() {
    return (_jsx("svg", { width: "16", height: "16", viewBox: "0 0 16 16", fill: "currentColor", "aria-hidden": "true", style: { display: "block", flexShrink: 0 }, children: _jsx("path", { d: "M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38\n        0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13\n        -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66\n        .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15\n        -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0\n        1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82\n        1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01\n        1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" }) }));
}
/* ─── Styles ─────────────────────────────────────────────────────────────── */
const styles = {
    footer: {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 24px",
        borderTop: "1px solid var(--color-border)",
        background: "var(--color-surface)",
        color: "var(--color-text-muted)",
        fontSize: 12,
    },
    credit: {
        color: "var(--color-text-muted)",
    },
    githubLink: {
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        color: "var(--color-text-muted)",
        textDecoration: "none",
        transition: "color 0.15s",
    },
    githubLabel: {
        fontSize: 12,
    },
};
