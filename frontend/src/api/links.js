import { request } from "./client";
export function createLink(data) {
    return request("/links", {
        method: "POST",
        body: JSON.stringify(data),
    });
}
export function listLinks(limit = 20, offset = 0) {
    return request(`/links?limit=${limit}&offset=${offset}`);
}
export function deleteLink(id) {
    return request(`/links/${id}`, { method: "DELETE" });
}
export function refetchLink(id) {
    return request(`/links/${id}/refetch`, { method: "POST" });
}
