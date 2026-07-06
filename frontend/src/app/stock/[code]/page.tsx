"use client";

import { use, useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import StockInput from "@/components/StockInput";
import KlineChart from "@/components/KlineChart";
import AnalyzePanel from "@/components/AnalyzePanel";
import { fetchStockDetail, fetchStockHistory, fetchStockIndicators } from "@/lib/api";
import type { ApiResponse, StockHistory, StockRealtime } from "@/lib/types";

export default function StockPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  const [stock, setStock] = useState<StockRealtime | null>(null);
  const [history, setHistory] = useState<StockHistory[]>([]);
  const [indicators, setIndicators] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const [stockResp, histResp, indResp] = await Promise.all([
          fetchStockDetail(code),
          fetchStockHistory(code),
          fetchStockIndicators(code),
        ]);
        if (!cancelled) {
          setStock((stockResp as ApiResponse<StockRealtime>).data);
          setHistory((histResp as ApiResponse<StockHistory[]>).data || []);
          setIndicators((indResp as ApiResponse<Record<string, unknown>>).data || null);
        }
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [code]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">{stock?.name || code}</h1>
            <p className="text-slate-500 text-sm">{code}</p>
          </div>
          <StockInput />
        </div>

        {loading ? (
          <div className="text-slate-500 text-center py-20">加载中...</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Chart area */}
            <div className="lg:col-span-3">
              {/* Price info bar */}
              {stock && (
                <div className="bg-slate-800/50 rounded-xl p-4 mb-4 flex gap-6">
                  <div>
                    <span className="text-3xl font-mono font-bold text-white">{stock.price?.toFixed(2)}</span>
                    <span className={`ml-3 text-lg ${stock.change_pct >= 0 ? "text-red-400" : "text-green-400"}`}>
                      {stock.change_pct >= 0 ? "+" : ""}
                      {stock.change_pct?.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex gap-4 text-sm text-slate-400">
                    <div>开盘: <span className="text-white">{stock.open?.toFixed(2)}</span></div>
                    <div>最高: <span className="text-white">{stock.high?.toFixed(2)}</span></div>
                    <div>最低: <span className="text-white">{stock.low?.toFixed(2)}</span></div>
                    <div>成交量: <span className="text-white">{(stock.volume / 10000).toFixed(0)}万</span></div>
                  </div>
                </div>
              )}

              {/* K-line chart */}
              <div className="bg-slate-800/50 rounded-xl p-4">
                <KlineChart
                  data={history}
                  indicators={indicators as { ma5?: number[]; ma10?: number[]; ma20?: number[]; macd?: { dif_list: number[]; dea_list: number[]; macd_list: number[] } } || undefined}
                />
              </div>
            </div>

            {/* Analysis panel */}
            <div>
              <AnalyzePanel stockCode={code} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
