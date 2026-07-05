"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPortfolios, PortfolioSummary } from "@/lib/api";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import PortfolioView from "@/components/PortfolioView";
import NotificationBell from "@/components/NotificationBell";

export default function PortfolioPage() {
  const [selected, setSelected] = useState<string>("");
  const { data, isLoading } = useQuery({
    queryKey: ["portfolios"],
    queryFn: fetchPortfolios,
  });

  const portfolios = data?.portfolios ?? [];

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">组合管理</h1>
          <NotificationBell />
        </header>
        <div className="flex gap-4">
          <aside className="w-48 space-y-2">
            {isLoading ? (
              <div className="animate-pulse h-20 bg-gray-100 dark:bg-gray-800 rounded" />
            ) : portfolios.length === 0 ? (
              <p className="text-sm text-gray-500">暂无组合。</p>
            ) : (
              portfolios.map((p: PortfolioSummary) => (
                <button
                  key={p.id}
                  onClick={() => setSelected(p.id)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors ${
                    selected === p.id
                      ? "bg-blue-100 dark:bg-blue-900/30"
                      : "hover:bg-gray-100 dark:hover:bg-gray-800"
                  }`}
                >
                  <div className="font-medium text-sm">{p.name}</div>
                  <div className="text-xs text-gray-500">
                    风险: {p.risk_score ?? 0}
                  </div>
                </button>
              ))
            )}
          </aside>
          <div className="flex-1">
            {selected ? (
              <PortfolioView portfolioId={selected} />
            ) : (
              <p className="text-gray-500">请从左侧选择一个组合。</p>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
