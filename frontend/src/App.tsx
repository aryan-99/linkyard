import { useState } from "react";
import LinksPage from "./pages/LinksPage";
import SearchPage from "./pages/SearchPage";
import SettingsPage from "./pages/SettingsPage";

type Tab = "links" | "search" | "settings";

export default function App() {
  const [tab, setTab] = useState<Tab>("links");

  const navStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 24px",
    height: 48,
    borderBottom: "1px solid var(--color-border)",
    background: "var(--color-surface)",
  };

  const brandStyle: React.CSSProperties = {
    fontWeight: 700,
    fontSize: 16,
    letterSpacing: "-0.01em",
    color: "var(--color-text-primary)",
    textDecoration: "none",
  };

  const tabGroupStyle: React.CSSProperties = {
    display: "flex",
    gap: 4,
    height: "100%",
    alignItems: "stretch",
  };

  function tabBtnStyle(active: boolean): React.CSSProperties {
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

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)" }}>
      <nav style={navStyle}>
        <span style={brandStyle}>Linkyard</span>
        <div style={tabGroupStyle}>
          <button
            onClick={() => setTab("links")}
            style={tabBtnStyle(tab === "links")}
            aria-current={tab === "links" ? "page" : undefined}
          >
            Links
          </button>
          <button
            onClick={() => setTab("search")}
            style={tabBtnStyle(tab === "search")}
            aria-current={tab === "search" ? "page" : undefined}
          >
            Search
          </button>
          <button
            onClick={() => setTab("settings")}
            style={tabBtnStyle(tab === "settings")}
            aria-current={tab === "settings" ? "page" : undefined}
          >
            Settings
          </button>
        </div>
      </nav>
      {tab === "links" && <LinksPage />}
      {tab === "search" && <SearchPage />}
      {tab === "settings" && <SettingsPage />}
    </div>
  );
}
