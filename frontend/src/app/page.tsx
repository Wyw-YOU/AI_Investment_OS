"use client";

import Sidebar from "@/components/Sidebar";
import StockInput from "@/components/StockInput";
import HotStocks from "@/components/HotStocks";
import { Providers } from "./providers";

export default function Dashboard() {
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
            {/* Market Overview */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-slate-800/50 rounded-xl p-4">
                <h3 className="text-sm font-medium text-slate-300 mb-3">  市场概览</h3>
                <div className="grid grid-cols-3 gap-4">
                  {["上证指数", "深证成指", "创业板指"].map((name) => (
                    <div key={name} className="bg-slate-900/50 rounded-lg p-3 text-center">
                      <p className="text-xs text-slate-500">{name}</p>
                      <p className="text-lg font-mono text-white mt-1">--</p>
                      <p className="text-xs text-slate-500 mt-0.5">--</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI Recommendations */}
              <div className="bg-slate-800/50 rounded-xl p-4">
                <h3 className="text-sm font-medium text-blue-400 mb-3">  AI 今日机会</h3>
                <p className="text-slate-500 text-sm">输入股票代码开始 AI 分析，获取投资建议</p>
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

            {/* Right sidebar */}
            <div>
              <HotStocks />
            </div>
          </div>
        </main>
      </div>
    </Providers>
  );
}
