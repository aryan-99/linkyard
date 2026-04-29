import { useEffect, useState } from "react";
import {
  getSettings,
  updateSettings,
  triggerReembed,
  type AppSettings,
} from "../api/settings";
import { setAuthToken } from "../api/client";

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Form state
  const [provider, setProvider] = useState<string>("local");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Admin token state
  const [adminToken, setAdminToken] = useState("");
  const [tokenSaved, setTokenSaved] = useState(false);

  // Re-embed state
  const [reembedding, setReembedding] = useState(false);
  const [reembedResult, setReembedResult] = useState<string | null>(null);
  const [reembedError, setReembedError] = useState<string | null>(null);

  // Load persisted admin token on mount
  useEffect(() => {
    const stored = localStorage.getItem("linkyard_admin_token");
    if (stored) {
      setAdminToken(stored);
      setAuthToken(stored);
    }
  }, []);

  useEffect(() => {
    getSettings()
      .then((data) => {
        setSettings(data);
        setProvider(data.embedding_provider);
      })
      .catch((err) => {
        setLoadError(err instanceof Error ? err.message : "Failed to load settings");
      });
  }, []);

  function handleSaveToken() {
    const trimmed = adminToken.trim();
    if (trimmed === "") {
      localStorage.removeItem("linkyard_admin_token");
      setAuthToken(null);
    } else {
      localStorage.setItem("linkyard_admin_token", trimmed);
      setAuthToken(trimmed);
    }
    setAdminToken(trimmed);
    setTokenSaved(true);
    setTimeout(() => setTokenSaved(false), 2500);
    // Re-fetch settings now that the token has changed.
    setLoadError(null);
    getSettings()
      .then((data) => {
        setSettings(data);
        setProvider(data.embedding_provider);
      })
      .catch((err) => {
        setLoadError(err instanceof Error ? err.message : "Failed to load settings");
      });
  }

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    const update = {
      embedding_provider: provider,
      ...(apiKey.trim() !== "" ? { openai_api_key: apiKey.trim() } : {}),
    };

    try {
      const updated = await updateSettings(update);
      setSettings(updated);
      setApiKey("");
      setSaveSuccess(true);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  async function handleClearKey() {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const updated = await updateSettings({ openai_api_key: null });
      setSettings(updated);
      setSaveSuccess(true);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to clear key");
    } finally {
      setSaving(false);
    }
  }

  async function handleReembed() {
    setReembedding(true);
    setReembedResult(null);
    setReembedError(null);

    try {
      const res = await triggerReembed();
      setReembedResult(`Re-embedded ${res.reembedded} link${res.reembedded !== 1 ? "s" : ""}`);
    } catch (err) {
      setReembedError(err instanceof Error ? err.message : "Re-embed failed");
    } finally {
      setReembedding(false);
    }
  }

  if (settings === null && !loadError) {
    return (
      <div style={styles.page}>
        <p style={styles.muted}>Loading settings…</p>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.pageTitle}>Settings</h1>

      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Admin Token</h2>
        <p style={styles.hint}>
          Required only when <code>ADMIN_TOKEN</code> is set on the server. Leave blank if not
          configured.
        </p>
        <label style={styles.label} htmlFor="admin-token-input">
          Admin token
        </label>
        <input
          id="admin-token-input"
          type="password"
          value={adminToken}
          onChange={(e) => setAdminToken(e.target.value)}
          placeholder="Leave blank if ADMIN_TOKEN is not set on the server"
          style={{ ...styles.input, marginBottom: 10 }}
          autoComplete="off"
        />
        <div style={styles.saveRow}>
          <button onClick={handleSaveToken} style={styles.secondaryBtn}>
            Save token
          </button>
          {tokenSaved && <span style={styles.success}>Token saved</span>}
        </div>
      </section>

      {loadError && (
        <p style={{ ...styles.error, marginBottom: 16 }}>{loadError}</p>
      )}

      {settings !== null && (
        <>
          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Embedding Provider</h2>

            <label style={styles.label} htmlFor="provider-select">
              Provider
            </label>
            <select
              id="provider-select"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              style={styles.select}
            >
              <option value="local">Local (no API key)</option>
              <option value="stub">Stub (testing only)</option>
              <option value="openai" disabled>
                OpenAI (coming soon)
              </option>
            </select>

            {provider === "local" && (
              <p style={styles.hint}>
                Using local sentence-transformers model (all-MiniLM-L6-v2). No API key required.
              </p>
            )}
            {provider === "stub" && (
              <p style={styles.hint}>
                Stub provider returns zero vectors. Intended for testing only.
              </p>
            )}
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>OpenAI API Key</h2>
            <p style={styles.hint}>
              Pre-configure your key for when OpenAI provider support is enabled.
            </p>

            {settings.has_openai_key && (
              <p style={styles.keyConfigured}>
                Key configured
                <button
                  onClick={handleClearKey}
                  disabled={saving}
                  style={styles.clearBtn}
                >
                  Clear key
                </button>
              </p>
            )}

            <label style={styles.label} htmlFor="api-key-input">
              {settings.has_openai_key ? "Replace key" : "API key"}
            </label>
            <input
              id="api-key-input"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={settings.has_openai_key ? "Enter new key to replace…" : "sk-…"}
              style={styles.input}
              autoComplete="off"
            />
          </section>

          <div style={styles.saveRow}>
            <button
              onClick={handleSave}
              disabled={saving}
              style={saving ? { ...styles.primaryBtn, ...styles.primaryBtnDisabled } : styles.primaryBtn}
            >
              {saving ? "Saving…" : "Save settings"}
            </button>
            {saveSuccess && <span style={styles.success}>Saved</span>}
            {saveError && <span style={styles.error}>{saveError}</span>}
          </div>
          <section style={{ ...styles.section, marginTop: 32 }}>
            <h2 style={styles.sectionTitle}>Re-embed Existing Links</h2>
            <p style={styles.hint}>
              If you recently changed providers, re-embed to update all stored vectors. This may take a
              moment depending on how many links you have saved.
            </p>

            <button
              onClick={handleReembed}
              disabled={reembedding}
              style={reembedding ? { ...styles.secondaryBtn, ...styles.secondaryBtnDisabled } : styles.secondaryBtn}
            >
              {reembedding ? "Re-embedding…" : "Re-embed all links"}
            </button>

            {reembedResult && <p style={styles.success}>{reembedResult}</p>}
            {reembedError && <p style={styles.error}>{reembedError}</p>}
          </section>
        </>
      )}
    </div>
  );
}

/* ─── Styles ──────────────────────────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  page: {
    maxWidth: 560,
    margin: "0 auto",
    padding: "32px 16px",
  },
  pageTitle: {
    fontSize: 22,
    fontWeight: 700,
    margin: "0 0 28px",
    color: "var(--color-text-primary)",
  },
  section: {
    marginBottom: 24,
    padding: 20,
    background: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 600,
    margin: "0 0 12px",
    color: "var(--color-text-primary)",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  label: {
    display: "block",
    fontSize: 13,
    fontWeight: 500,
    color: "var(--color-text-secondary)",
    marginBottom: 6,
  },
  select: {
    width: "100%",
    padding: "8px 10px",
    fontSize: 14,
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    background: "var(--color-bg)",
    color: "var(--color-text-primary)",
    fontFamily: "inherit",
    cursor: "pointer",
  },
  input: {
    width: "100%",
    padding: "8px 10px",
    fontSize: 14,
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    background: "var(--color-bg)",
    color: "var(--color-text-primary)",
    fontFamily: "inherit",
  },
  hint: {
    fontSize: 13,
    color: "var(--color-text-muted)",
    margin: "8px 0 0",
    lineHeight: 1.5,
  },
  keyConfigured: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    fontSize: 13,
    color: "var(--color-success)",
    fontWeight: 500,
    margin: "0 0 12px",
  },
  clearBtn: {
    background: "none",
    border: "1px solid var(--color-border)",
    borderRadius: 4,
    color: "var(--color-text-secondary)",
    cursor: "pointer",
    fontSize: 12,
    padding: "2px 8px",
    fontFamily: "inherit",
  },
  saveRow: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    marginBottom: 8,
  },
  primaryBtn: {
    padding: "9px 20px",
    fontSize: 14,
    fontWeight: 500,
    background: "var(--color-accent)",
    color: "var(--color-btn-primary-text, #ffffff)",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "opacity 0.15s",
  },
  primaryBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
  secondaryBtn: {
    padding: "9px 20px",
    fontSize: 14,
    fontWeight: 500,
    background: "var(--color-surface)",
    color: "var(--color-text-secondary)",
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "opacity 0.15s",
  },
  secondaryBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
  success: {
    fontSize: 13,
    color: "var(--color-success)",
    margin: "8px 0 0",
  },
  error: {
    fontSize: 13,
    color: "var(--color-error)",
    margin: "8px 0 0",
  },
  muted: {
    color: "var(--color-text-muted)",
    fontSize: 14,
  },
};
