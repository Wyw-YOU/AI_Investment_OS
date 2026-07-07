"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import StockInput from "@/components/StockInput";
import HotStocks from "@/components/HotStocks";
import { fetchMarketOverview, fetchAnalysisHistory } from "@/lib/api";
import type { ApiResponse } from "@/lib/types";
import { Providers } from "./providers";

interface MarketIndex {
  name: string;
  close: number;
  change_pct: number;
}

interface RecentTask {
  task_id: number;
  stock_code: string;
  status: string;
  created_at: string;
}

const STATUS_LABELS: Record<string, { text: string; color: string }> = {
  complete: { text: "完成", color: "text-green-400" },
  running: { text: "运行中", color: "text-blue-400" },
  pending: { text: "等待中", color: "text-yellow-400" },
  failed: { text: "失败", color: "text-red-400" },
};

export default function Dashboard() {
  const [overview, setOverview] = useState<Record<string, MarketIndex>>({});
  const [recentTasks, setRecentTasks] = useState<RecentTask[]>([]);

  useEffect(() => {
    fetchMarketOverview()
      .then((r: ApiResponse<Record<string, MarketIndex>>) => setOverview(r.data || {}))
      .catch(() => {});
    fetchAnalysisHistory()
      .then((r: ApiResponse<RecentTask[]>) => setRecentTasks((r.data || []).slice(0, 5)))
      .catch(() => {});
  }, []);

  const indices = [
    { code: "000001", fallback: "上证指数" },
    { code: "399001", fallback: "深证成指" },
    { code: "399006", fallback: "创业板指" },
  ];

  return (
    <Providers>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-white">Dashboard</h1>
              <p className="text-slate-500 text-sm mt-1">AI 驱动的投资研究操作系统</p>
            </div>
            <StockInput />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Market Overview - live data */}
              <div className="bg-slate-800/50 rounded-xl p-4">
                <h3 className="text-sm font-medium text-slate-300 mb-3">  市场概览</h3>
                <div className="grid grid-cols-3 gap-4">
                  {indices.map(({ code, fallback }) => {
                    const idx = overview[code];
                    const name = idx?.name || fallback;
                    const close = idx?.close || 0;
                    const pct = idx?.change_pct || 0;
                    return (
                      <div key={code} className="bg-slate-900/50 rounded-lg p-3 text-center">
                        <p className="text-xs text-slate-500">{name}</p>
                        <p className="text-lg font-mono text-white mt-1">
                          {close ? close.toFixed(2) : "--"}
                        </p>
                        <p className={`text-xs mt-0.5 ${pct >= 0 ? "text-red-400" : "text-green-400"}`}>
                          {close ? `${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%` : "--"}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recent Analyses */}
              <div className="bg-slate-800/50 rounded-xl p-4">
                <h3 className="text-sm font-medium text-blue-400 mb-3">  最近分析</h3>
                {recentTasks.length === 0 ? (
                  <p className="text-slate-500 text-sm">暂无分析记录，输入股票代码开始 AI 分析</p>
                ) : (
                  <div className="space-y-2">
                    {recentTasks.map((task) => {
                      const s = STATUS_LABELS[task.status] || { text: task.status, color: "text-slate-400" };
                      return (
                        <a
                          key={task.task_id}
                          href={`/stock/${task.stock_code}`}
                          className="flex items-center justify-between py-2 px-3 hover:bg-slate-700/50 rounded-lg"
                        >
                          <div>
                            <span className="text-white text-sm font-medium">{task.stock_code}</span>
                            <span className="text-slate-500 text-xs ml-2">
                              {new Date(task.created_at).toLocaleString("zh-CN")}
                            </span>
                          </div>
                          <span className={`text-xs ${s.color}`}>{s.text}</span>
                        </a>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Agent Status */}
              <div className="bg-slate-800/50 rounded-xl p-4">
                <h3 className="text-sm font-medium text-green-400 mb-3">  Agent 系统状态</h3>
                <div className="grid grid-cols-4 gap-2">
                  {["Planner", "News", "Financial", "Technical", "Macro", "Risk", "Quant", "Report"].map((name) => (
                    <div key={name} className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="text-slate-400">{name}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <HotStocks />
            </div>
          </div>
        </main>
      </div>
    </Providers>
  );
}
