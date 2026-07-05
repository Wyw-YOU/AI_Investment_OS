const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export interface HotStock {
  stock_code: string;
  name: string;
  latest_price: number;
  change_pct: number;
  amount: number;
}

export interface PortfolioSummary {
  id: string;
  name: string;
  holdings: Record<string, number>;
  candidate_pool: string[];
  risk_score: number;
  expected_return: number;
}

export interface PortfolioDetail extends PortfolioSummary {}

export interface Alert {
  id: number;
  stock_code: string;
  alert_type: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface AnalysisResult {
  status: string;
  stock: string;
  decision: string;
  report: Record<string, unknown>;
  agent_outputs: Record<string, unknown>;
  agent_confidence: Record<string, number>;
}

export const fetchHotStocks = () =>
  apiFetch<{ stocks: HotStock[] }>("/api/stocks/hot");

export const analyzeStock = (stockCode: string) =>
  apiFetch<AnalysisResult>(`/api/stocks/analyze/sync/${stockCode}`);

export const fetchStockDetail = (code: string) =>
  apiFetch<Record<string, unknown>>(`/api/stocks/${code}`);

export const fetchPortfolios = () =>
  apiFetch<{ portfolios: PortfolioSummary[] }>("/api/portfolio/");

export const fetchPortfolioDetail = (id: string) =>
  apiFetch<PortfolioDetail>(`/api/portfolio/${id}`);

export const createPortfolio = (name: string) =>
  apiFetch<{ id: string; name: string; status: string }>(
    `/api/portfolio/?name=${encodeURIComponent(name)}`,
    { method: "POST" }
  );

export const suggestWeights = (id: string) =>
  apiFetch<{ weights: Record<string, number>; scores: Record<string, number> }>(
    `/api/portfolio/${id}/suggest-weights`,
    { method: "POST" }
  );

export const calcRisk = (id: string) =>
  apiFetch<{
    risk_score: number;
    risk_level: string;
    sector_exposure: Record<string, number>;
    max_single_weight: number;
    risk_factors: string[];
  }>(`/api/portfolio/${id}/risk`);

export const fetchAlerts = (userId = "default") =>
  apiFetch<{ alerts: Alert[] }>(`/api/alerts/?user_id=${userId}`);

export const fetchUnreadAlerts = (userId = "default") =>
  apiFetch<{ alerts: Alert[]; count: number }>(
    `/api/alerts/unread?user_id=${userId}`
  );
