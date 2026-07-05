"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPortfolioDetail } from "@/lib/api";

export default function PortfolioView({ portfolioId }: { portfolioId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["portfolio", portfolioId],
    queryFn: () => fetchPortfolioDetail(portfolioId),
    enabled: !!portfolioId,
  });

  if (isLoading) return <div className="animate-pulse h-60 bg-gray-100 dark:bg-gray-800 rounded" />;
  if (!data) return <p className="text-gray-500">请选择一个组合</p>;

  const holdings = data.holdings ?? {};
  const entries = Object.entries(holdings) as [string, number][];
  const total = entries.reduce((s, [, w]) => s + w, 0);

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">{data.name}</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="border rounded p-3 dark:border-gray-800">
          <div className="text-sm text-gray-500">风险评分</div>
          <div className="text-2xl font-bold">{data.risk_score ?? 0}</div>
        </div>
        <div className="border rounded p-3 dark:border-gray-800">
          <div className="text-sm text-gray-500">持仓数量</div>
          <div className="text-2xl font-bold">{entries.length}</div>
        </div>
        <div className="border rounded p-3 dark:border-gray-800">
          <div className="text-sm text-gray-500">总权重</div>
          <div className="text-2xl font-bold">{(total * 100).toFixed(1)}%</div>
        </div>
      </div>
      {entries.length > 0 && (
        <div className="border rounded p-4 dark:border-gray-800">
          <h3 className="font-semibold mb-2">持仓明细</h3>
          <div className="space-y-2">
            {entries.map(([code, weight]) => (
              <div key={code} className="flex items-center gap-2">
                <span className="w-20 text-sm font-mono">{code}</span>
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                  <div
                    className="bg-blue-600 h-4 rounded-full"
                    style={{ width: `${(weight / Math.max(total, 0.01)) * 100}%` }}
                  />
                </div>
                <span className="w-14 text-right text-sm">{(weight * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
