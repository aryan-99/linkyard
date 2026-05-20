import { useEffect, useState } from "react";
import {
  getSettings,
  updateSettings,
  triggerReembed,
  refetchAllLinks,
  type AppSettings,
} from "../api/settings";
import { setAuthToken } from "../api/client";

/* ─── ConfirmDialog (co-located, only used in this page) ──────────────────── */

interface ConfirmDialogProps {
  title: string;
  children: React.ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({ title, children, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <div style={dialogStyles.backdrop} onClick={onCancel}>
      <div
        style={dialogStyles.card}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
      >
        <h3 id="confirm-dialog-title" style={dialogStyles.title}>{title}</h3>
        <div style={dialogStyles.body}>{children}</div>
        <div style={dialogStyles.actions}>
          <button onClick={onCancel} style={dialogStyles.cancelBtn}>Cancel</button>
          <button onClick={onConfirm} style={dialogStyles.confirmBtn}>Confirm</button>
        </div>
      </div>
    </div>
  );
}

const dialogStyles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.4)",
    zIndex: 100,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    background: "var(--color-bg)",
    border: "1px solid var(--color-border)",
    borderRadius: 10,
    padding: "24px 28px",
    maxWidth: 440,
    width: "calc(100% - 32px)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.18)",
  },
  title: {
    margin: "0 0 12px",
    fontSize: 16,
    fontWeight: 600,
    color: "var(--color-text-primary)",
  },
  body: {
    fontSize: 14,
    color: "var(--color-text-secondary)",
    lineHeight: 1.55,
    marginBottom: 20,
  },
  actions: {
    display: "flex",
    justifyContent: "flex-end",
    gap: 10,
  },
  cancelBtn: {
    padding: "8px 18px",
    fontSize: 14,
    fontWeight: 500,
    background: "var(--color-surface)",
    color: "var(--color-text-secondary)",
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    cursor: "pointer",
    fontFamily: "inherit",
  },
  confirmBtn: {
    padding: "8px 18px",
    fontSize: 14,
    fontWeight: 500,
    background: "transparent",
    color: "var(--color-accent)",
    border: "1.5px solid var(--color-accent)",
    borderRadius: 6,
    cursor: "pointer",
    fontFamily: "inherit",
  },
};

/* ─── SettingsPage ────────────────────────────────────────────────────────── */

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Form state
  const [provider, setProvider] = useState<string>("local");
  const [apiKey, setApiKey] = useState("");
  const [threshold, setThreshold] = useState<number>(0.3);
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
  const [showReembedConfirm, setShowReembedConfirm] = useState(false);

  // Re-fetch state
  const [refetching, setRefetching] = useState(false);
  const [refetchResult, setRefetchResult] = useState<string | null>(null);
  const [refetchError, setRefetchError] = useState<string | null>(null);
  const [showRefetchConfirm, setShowRefetchConfirm] = useState(false);
  const [refetchForce, setRefetchForce] = useState(false);

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
        setThreshold(data.search_threshold);
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
        setThreshold(data.search_threshold);
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
      search_threshold: threshold,
      ...(apiKey.trim() !== "" ? { openai_api_key: apiKey.trim() } : {}),
    };

    try {
      const updated = await updateSettings(update);
      setSettings(updated);
      setThreshold(updated.search_threshold);
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
    setShowReembedConfirm(false);
    setReembedding(true);
    setReembedResult(null);
    setReembedError(null);

    try {
      const res = await triggerReembed();
      setReembedResult(`Re-embedded ${res.reembedded} link${res.reembedded !== 1 ? "s" : ""}.`);
    } catch (err) {
      setReembedError(err instanceof Error ? err.message : "Re-embed failed");
    } finally {
      setReembedding(false);
    }
  }

  async function handleRefetchAll() {
    setShowRefetchConfirm(false);
    setRefetching(true);
    setRefetchResult(null);
    setRefetchError(null);

    try {
      const res = await refetchAllLinks(refetchForce);
      setRefetchResult(`Re-fetched ${res.refetched} link${res.refetched !== 1 ? "s" : ""}.`);
    } catch (err) {
      setRefetchError(err instanceof Error ? err.message : "Re-fetch failed");
    } finally {
      setRefetching(false);
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

      {/* ── Re-embed confirm dialog ── */}
      {showReembedConfirm && (
        <ConfirmDialog
          title="Re-embed all links"
          onConfirm={handleReembed}
          onCancel={() => setShowReembedConfirm(false)}
        >
          This will re-embed all saved links using their stored content. Links without fetched page
          content will use title and snippet only. Continue?
        </ConfirmDialog>
      )}

      {/* ── Re-fetch confirm dialog ── */}
      {showRefetchConfirm && (
        <ConfirmDialog
          title="Re-fetch page content"
          onConfirm={handleRefetchAll}
          onCancel={() => setShowRefetchConfirm(false)}
        >
          <p style={{ margin: "0 0 12px" }}>
            By default, only links where no page content has been captured yet will be fetched. Check
            the box below to re-fetch all links, including those already indexed.
          </p>
          <label style={dialogStyles.checkboxLabel}>
            <input
              type="checkbox"
              checked={refetchForce}
              onChange={(e) => setRefetchForce(e.target.checked)}
              style={{ marginRight: 8 }}
            />
            Re-fetch all links, including those already indexed
          </label>
        </ConfirmDialog>
      )}

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
                OpenAI — coming soon
              </option>
            </select>

            {/* Coming-soon notice — always visible so users know OpenAI isn't functional yet */}
            <p style={styles.comingSoonNote}>
              <strong>OpenAI provider is not yet available.</strong> Only Local and Stub are
              functional. OpenAI support (1536-dim, text-embedding-3-small) is planned for v1.1.
            </p>

            {/* Warn when the dropdown value differs from the last-saved value */}
            {settings.embedding_provider !== provider && (
              <p style={styles.providerWarning}>
                Changing the embedding provider requires a full re-embed of all links. Use
                "Re-embed all links" below after saving.
              </p>
            )}

            {provider === "local" && (
              <p style={styles.hint}>
                Using local sentence-transformers model (multi-qa-MiniLM-L6-cos-v1). No API key required.
              </p>
            )}
            {provider === "stub" && (
              <p style={styles.hint}>
                Stub provider returns zero vectors. Intended for testing only.
              </p>
            )}
          </section>

          <section style={styles.section}>
            <h2 style={styles.sectionTitle}>Search Threshold</h2>
            <p style={styles.hint}>
              Minimum similarity score (0–1) a result must reach to appear in search. Higher values
              return fewer but more relevant results. Default: 0.30.
            </p>
            <label style={styles.label} htmlFor="threshold-input">
              Score threshold
            </label>
            <input
              id="threshold-input"
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={threshold}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                if (!isNaN(val)) setThreshold(Math.min(1, Math.max(0, val)));
              }}
              style={{ ...styles.input, width: 100 }}
            />
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
              onClick={() => setShowReembedConfirm(true)}
              disabled={reembedding}
              style={reembedding ? { ...styles.secondaryBtn, ...styles.secondaryBtnDisabled } : styles.secondaryBtn}
            >
              {reembedding ? "Re-embedding…" : "Re-embed all links"}
            </button>

            {reembedResult && <p style={styles.success}>{reembedResult}</p>}
            {reembedError && <p style={styles.error}>{reembedError}</p>}
          </section>

          <section style={{ ...styles.section, marginTop: 16 }}>
            <h2 style={styles.sectionTitle}>Re-fetch Page Content</h2>
            <p style={styles.hint}>
              Re-fetches page body content from the source URL and re-embeds the link. By default,
              only links where no content has been captured yet are fetched.
            </p>

            <button
              onClick={() => {
                setRefetchForce(false);
                setShowRefetchConfirm(true);
              }}
              disabled={refetching}
              style={refetching ? { ...styles.secondaryBtn, ...styles.secondaryBtnDisabled } : styles.secondaryBtn}
            >
              {refetching ? "Re-fetching…" : "Re-fetch all"}
            </button>

            {refetchResult && <p style={styles.success}>{refetchResult}</p>}
            {refetchError && <p style={styles.error}>{refetchError}</p>}
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
  comingSoonNote: {
    fontSize: 12,
    color: "var(--color-text-muted)",
    background: "var(--color-accent-tint)",
    border: "1px solid var(--color-border)",
    borderRadius: 4,
    padding: "7px 10px",
    margin: "10px 0 0",
    lineHeight: 1.5,
  },
  providerWarning: {
    fontSize: 13,
    fontWeight: 500,
    color: "var(--color-warning)",
    background: "var(--color-warning-tint)",
    border: "1px solid var(--color-warning)",
    borderRadius: 4,
    padding: "8px 10px",
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
    background: "transparent",
    color: "var(--color-accent)",
    border: "1.5px solid var(--color-accent)",
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

// Augment dialogStyles with the checkbox label (needs to live with dialogStyles for co-location)
dialogStyles.checkboxLabel = {
  display: "flex",
  alignItems: "flex-start",
  fontSize: 13,
  color: "var(--color-text-secondary)",
  cursor: "pointer",
  lineHeight: 1.5,
} as React.CSSProperties;
