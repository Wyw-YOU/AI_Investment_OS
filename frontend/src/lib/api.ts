import type { AnalysisProgressEvent } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    const wsBase = API_BASE.replace("http://", "ws://").replace("https://", "wss://");
    const ws = new WebSocket(`${wsBase}/api/agent/ws/analysis/${analysisId}`);
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
