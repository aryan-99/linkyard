import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import LinksPage from "./pages/LinksPage";
import SearchPage from "./pages/SearchPage";
import SettingsPage from "./pages/SettingsPage";
import { Footer } from "./components/Footer";
export default function App() {
    const [tab, setTab] = useState("links");
    const navStyle = {
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 24px",
        height: 48,
        borderBottom: "1px solid var(--color-border)",
        background: "var(--color-surface)",
    };
    const brandStyle = {
        fontWeight: 700,
        fontSize: 16,
        letterSpacing: "-0.01em",
        color: "var(--color-text-primary)",
        textDecoration: "none",
    };
    const tabGroupStyle = {
        display: "flex",
        gap: 4,
        height: "100%",
        alignItems: "stretch",
    };
    function tabBtnStyle(active) {
        return {
            background: "none",
            border: "none",
            borderBottom: active ? "2px solid var(--color-accent)" : "2px solid transparent",
            color: active ? "var(--color-accent)" : "var(--color-text-secondary)",
            cursor: "pointer",
            fontSize: 14,
            fontFamily: "inherit",
            fontWeight: active ? 500 : 400,
            padding: "0 12px",
            transition: "color 0.15s, border-color 0.15s",
        };
    }
    return (_jsxs("div", { style: {
            minHeight: "100vh",
            background: "var(--color-bg)",
            display: "flex",
            flexDirection: "column",
        }, children: [_jsxs("nav", { style: navStyle, children: [_jsx("span", { style: brandStyle, children: "Linkyard" }), _jsxs("div", { style: tabGroupStyle, children: [_jsx("button", { onClick: () => setTab("links"), style: tabBtnStyle(tab === "links"), "aria-current": tab === "links" ? "page" : undefined, children: "Links" }), _jsx("button", { onClick: () => setTab("search"), style: tabBtnStyle(tab === "search"), "aria-current": tab === "search" ? "page" : undefined, children: "Search" }), _jsx("button", { onClick: () => setTab("settings"), style: tabBtnStyle(tab === "settings"), "aria-current": tab === "settings" ? "page" : undefined, children: "Settings" })] })] }), _jsxs("main", { style: { flex: 1 }, children: [tab === "links" && _jsx(LinksPage, {}), tab === "search" && _jsx(SearchPage, {}), tab === "settings" && _jsx(SettingsPage, {})] }), _jsx(Footer, {})] }));
}
