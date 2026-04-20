import { useState } from "react";
import { createLink, type LinkDetailResponse } from "../api/links";

interface Props {
  onCreated: (link: LinkDetailResponse) => void;
}

export default function AddLinkForm({ onCreated }: Props) {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [snippet, setSnippet] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const link = await createLink({
        url,
        title: title || undefined,
        snippet: snippet || undefined,
        source: "web",
      });
      setUrl("");
      setTitle("");
      setSnippet("");
      onCreated(link);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save link");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h2 style={styles.heading}>Save a link</h2>
      <div style={styles.field}>
        <label style={styles.label} htmlFor="url">
          URL <span style={styles.required}>*</span>
        </label>
        <input
          id="url"
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article"
          style={styles.input}
          disabled={loading}
        />
      </div>
      <div style={styles.field}>
        <label style={styles.label} htmlFor="title">
          Title
        </label>
        <input
          id="title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Optional title"
          style={styles.input}
          disabled={loading}
        />
      </div>
      <div style={styles.field}>
        <label style={styles.label} htmlFor="snippet">
          Snippet
        </label>
        <textarea
          id="snippet"
          value={snippet}
          onChange={(e) => setSnippet(e.target.value)}
          placeholder="Optional short description"
          style={{ ...styles.input, height: 72, resize: "vertical" }}
          disabled={loading}
        />
      </div>
      {error && <p style={styles.error}>{error}</p>}
      <button type="submit" disabled={loading} style={styles.button}>
        {loading ? "Saving…" : "Save link"}
      </button>
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    background: "var(--color-surface)",
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    padding: "16px 20px",
    marginBottom: 32,
    maxWidth: 560,
  },
  heading: {
    margin: "0 0 14px",
    fontSize: 15,
    fontWeight: 600,
    color: "var(--color-text-primary)",
  },
  field: { display: "flex", flexDirection: "column", marginBottom: 10 },
  label: {
    fontSize: 13,
    fontWeight: 500,
    marginBottom: 4,
    color: "var(--color-text-secondary)",
  },
  required: { color: "var(--color-error)" },
  input: {
    padding: "7px 10px",
    border: "1px solid var(--color-border)",
    borderRadius: 6,
    fontSize: 14,
    fontFamily: "inherit",
    background: "var(--color-bg)",
    color: "var(--color-text-primary)",
    outline: "none",
  },
  error: {
    color: "var(--color-error)",
    fontSize: 13,
    margin: "8px 0",
  },
  button: {
    marginTop: 6,
    padding: "8px 20px",
    background: "var(--color-accent)",
    color: "#ffffff",
    border: "none",
    borderRadius: 4,
    fontSize: 14,
    cursor: "pointer",
    fontFamily: "inherit",
  },
};
