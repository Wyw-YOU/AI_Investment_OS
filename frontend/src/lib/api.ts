/**
 * API 客户端层。
 *
 * 设计要点：
 * - API_BASE 为空字符串，所有请求走 Next.js rewrite 代理（/api/* → backend:8000），
 *   这样浏览器端不需要知道后端地址，也避免 CORS 问题。
 * - WebSocket 无法被 Next.js 代理，需直连后端 8000 端口。
 * - SSR 和 CSR 统一用相同路径，rewrites 在服务端同样生效。
 */

import type { AnalysisProgressEvent } from "./types";

// Use empty string so requests go through Next.js rewrite proxy in production.
// In standalone Docker, Next.js rewrites /api/* to backend container.
const API_BASE = "";

async function fetchApi(path: string, options: RequestInit = {}) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: token ? `Bearer ${token}` : "",
      ...options.headers,
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.message || "Request failed");
  return data;
}

// Auth
export const login = (email: string, password: string) =>
  fetchApi("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });

export const register = (email: string, password: string) =>
  fetchApi("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });

export const getMe = () => fetchApi("/api/auth/me");

// Stocks
export const fetchHotStocks = () => fetchApi("/api/stocks/hot");
export const fetchStockDetail = (code: string) => fetchApi(`/api/stocks/${code}`);
export const fetchStockHistory = (code: string) => fetchApi(`/api/stocks/${code}/history`);
export const fetchStockIndicators = (code: string) => fetchApi(`/api/stocks/${code}/indicators`);
export const fetchMarketOverview = () => fetchApi("/api/market/overview");

// Agent
export const startAnalysis = (stockCode: string, query?: string) =>
  fetchApi("/api/agent/run", {
    method: "POST",
    body: JSON.stringify({ stock_code: stockCode, query: query || "" }),
  });

export const getAnalysisStatus = (taskId: number) => fetchApi(`/api/agent/status/${taskId}`);
export const getAnalysisProgress = (analysisId: string) => fetchApi(`/api/agent/progress/${analysisId}`);
export const fetchAnalysisHistory = () => fetchApi("/api/agent/history");

export function connectAnalysisWS(
  analysisId: string,
  onEvent: (event: AnalysisProgressEvent) => void,
): WebSocket | null {
  if (typeof window === "undefined") return null;
  try {
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    // WebSocket connects directly to backend port (Next.js cannot proxy WS)
    const wsHost = `${window.location.hostname}:8000`;
    const ws = new WebSocket(`${wsProto}//${wsHost}/api/agent/ws/analysis/${analysisId}`);
    ws.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data));
      } catch {}
    };
    ws.onerror = () => {};
    return ws;
  } catch {
    return null;
  }
}

// Workspace
export const fetchWorkspaces = () => fetchApi("/api/workspace");
export const createWorkspace = (stockCode: string, name?: string) =>
  fetchApi("/api/workspace", {
    method: "POST",
    body: JSON.stringify({ stock_code: stockCode, name: name || "" }),
  });
export const fetchWorkspaceDetail = (id: number) => fetchApi(`/api/workspace/${id}`);
export const fetchWorkspaceAnalyses = (id: number) => fetchApi(`/api/workspace/${id}/analyses`);
export const fetchWorkspaceTimeline = (id: number) => fetchApi(`/api/workspace/${id}/timeline`);
