import { request } from "./client";
export function getSettings() {
    return request("/settings");
}
export function updateSettings(update) {
    return request("/settings", {
        method: "PUT",
        body: JSON.stringify(update),
    });
}
export function triggerReembed() {
    return request("/settings/reembed", {
        method: "POST",
    });
}
export function refetchAllLinks(force) {
    return request("/settings/refetch", {
        method: "POST",
        body: JSON.stringify({ force }),
    });
}
