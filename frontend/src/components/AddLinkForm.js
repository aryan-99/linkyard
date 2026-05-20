import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { createLink } from "../api/links";
export default function AddLinkForm({ onCreated }) {
    const [url, setUrl] = useState("");
    const [title, setTitle] = useState("");
    const [snippet, setSnippet] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    async function handleSubmit(e) {
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
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to save link");
        }
        finally {
            setLoading(false);
        }
    }
    return (_jsxs("form", { onSubmit: handleSubmit, style: styles.form, children: [_jsx("h2", { style: styles.heading, children: "Save a link" }), _jsxs("div", { style: styles.field, children: [_jsxs("label", { style: styles.label, htmlFor: "url", children: ["URL ", _jsx("span", { style: styles.required, children: "*" })] }), _jsx("input", { id: "url", type: "url", required: true, value: url, onChange: (e) => setUrl(e.target.value), placeholder: "https://example.com/article", style: styles.input, disabled: loading })] }), _jsxs("div", { style: styles.field, children: [_jsx("label", { style: styles.label, htmlFor: "title", children: "Title" }), _jsx("input", { id: "title", type: "text", value: title, onChange: (e) => setTitle(e.target.value), placeholder: "Optional title", style: styles.input, disabled: loading })] }), _jsxs("div", { style: styles.field, children: [_jsx("label", { style: styles.label, htmlFor: "snippet", children: "Snippet" }), _jsx("textarea", { id: "snippet", value: snippet, onChange: (e) => setSnippet(e.target.value), placeholder: "Optional short description", style: { ...styles.input, height: 72, resize: "vertical" }, disabled: loading })] }), error && _jsx("p", { style: styles.error, children: error }), _jsx("button", { type: "submit", disabled: loading, style: styles.button, children: loading ? "Saving…" : "Save link" })] }));
}
const styles = {
    form: {
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: 6,
        padding: "16px 20px",
        marginBottom: 32,
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
        background: "transparent",
        color: "var(--color-accent)",
        border: "1.5px solid var(--color-accent)",
        borderRadius: 6,
        fontSize: 14,
        fontWeight: 500,
        cursor: "pointer",
        fontFamily: "inherit",
    },
};
