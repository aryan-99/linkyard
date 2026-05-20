export const BASE = "http://localhost:8000";
let authToken = null;
/** Call with a non-empty string to send `Authorization: Bearer <token>` on every request.
 *  Call with null or empty string to stop sending the header. */
export function setAuthToken(token) {
    authToken = token && token.length > 0 ? token : null;
}
export async function request(path, init) {
    const authHeader = authToken !== null ? { Authorization: `Bearer ${authToken}` } : {};
    const res = await fetch(`${BASE}${path}`, {
        headers: { "Content-Type": "application/json", ...authHeader },
        ...init,
    });
    if (!res.ok) {
        const detail = await res.text().catch(() => res.statusText);
        throw new Error(`${res.status}: ${detail}`);
    }
    if (res.status === 204)
        return undefined;
    return res.json();
}
