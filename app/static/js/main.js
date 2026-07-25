// AI 财报智审助手 - 全局工具函数
const API_BASE = "/api";
async function api(method, path, body) {
    const opts = { method, headers: { "Content-Type": "application/json" } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API_BASE + path, opts);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `请求失败 (${res.status})`);
    }
    return res.json();
}
function getStorage(key, def = null) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : def; }
    catch { return def; }
}
function setStorage(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
}
function removeStorage(key) {
    try { localStorage.removeItem(key); } catch {}
}
function getSession(key, def = null) {
    try { const v = sessionStorage.getItem(key); return v ? JSON.parse(v) : def; }
    catch { return def; }
}
function setSession(key, val) {
    try { sessionStorage.setItem(key, JSON.stringify(val)); } catch {}
}
function removeSession(key) {
    try { sessionStorage.removeItem(key); } catch {}
}
function showAlert(containerId, type, message) {
    const c = document.getElementById(containerId);
    if (!c) return;
    c.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
}
function clearAlert(containerId) {
    const c = document.getElementById(containerId);
    if (c) c.innerHTML = "";
}
function getApiKey() { return getStorage("api_key", ""); }
function getProvider() { return getStorage("provider", "openai"); }
function getModel() { return getStorage("model", ""); }
function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
}
function escapeHtml(text) {
    const d = document.createElement("div");
    d.textContent = text;
    return d.innerHTML;
}
function formatAnswer(text) {
    return text
        .replace(/【(\d+)页】/g, '<span class="source">【第$1页】</span>')
        .replace(/\n/g, "<br>");
}
