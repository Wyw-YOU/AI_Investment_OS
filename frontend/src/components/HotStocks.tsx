"use client";

import useSWR from "swr";
import { fetchHotStocks } from "@/lib/api";
import type { ApiResponse, StockRealtime } from "@/lib/types";

export default function HotStocks() {
  const { data, error, isLoading } = useSWR<ApiResponse<StockRealtime[]>>("/api/stocks/hot", fetchHotStocks);

  if (isLoading) return <div className="text-slate-500 text-sm">加载中...</div>;
  if (error || !data?.data) return <div className="text-slate-500 text-sm">暂无数据</div>;

  const stocks = data.data.slice(0, 10);

  return (
    <div className="bg-slate-800/50 rounded-xl p-4">
      <h3 className="text-sm font-medium text-slate-300 mb-3">  热门股票</h3>
      <div className="space-y-2">
        {stocks.map((stock) => (
          <a
            key={stock.code}
            href={`/stock/${stock.code}`}
            className="flex items-center justify-between py-1.5 px-2 hover:bg-slate-700/50 rounded text-sm"
          >
            <div>
              <span className="text-white">{stock.name}</span>
              <span className="text-slate-500 ml-2 text-xs">{stock.code}</span>
            </div>
            <span className={stock.change_pct >= 0 ? "text-red-400" : "text-green-400"}>
              {stock.change_pct >= 0 ? "+" : ""}
              {stock.change_pct?.toFixed(2)}%
            </span>
          </a>
        ))}
      </div>
    </div>
  );
}
