export interface StockRealtime {
  code: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
  market_cap: number;
  pe: number;
  pb: number;
}

export interface StockHistory {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
}

export interface AgentOutput {
  agent_name: string;
  result: Record<string, unknown>;
  confidence: number;
  citations: string[];
}

export interface AnalysisResult {
  task_id: number;
  stock_code: string;
  stock_name: string;
  phase: string;
  final_report: {
    executive_summary?: string;
    recommendation?: string;
    target_price?: { low: number; high: number };
    key_findings?: string[];
    overall_score?: number;
  };
  risk_assessment: {
    overall_risk?: string;
    risk_score?: number;
  };
  quant_score: {
    composite_score?: number;
    rating?: string;
  };
  agent_outputs: Record<string, { confidence: number; summary: string }>;
}

export interface Workspace {
  id: number;
  stock_code: string;
  name: string;
  created_at: string;
}

export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}
