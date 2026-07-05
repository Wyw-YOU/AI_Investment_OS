"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchHotStocks, HotStock } from "@/lib/api";

export default function HotStocks() {
  const { data, isLoading } = useQuery({
    queryKey: ["hot-stocks"],
    queryFn: fetchHotStocks,
  });

  if (isLoading) return <div className="animate-pulse h-40 bg-gray-100 dark:bg-gray-800 rounded" />;

  const stocks = data?.stocks ?? [];

  return (
    <div className="border rounded-lg p-4 dark:border-gray-800">
      <h2 className="font-semibold mb-3">Hot Stocks</h2>
      {stocks.length === 0 ? (
        <p className="text-sm text-gray-500">No data yet. Start backend to load.</p>
      ) : (
        <div className="space-y-2">
          {stocks.map((s: HotStock) => (
            <div key={s.stock_code} className="flex justify-between text-sm">
              <span>{s.name} ({s.stock_code})</span>
              <span className={s.change_pct >= 0 ? "text-red-600" : "text-green-600"}>
                {s.change_pct >= 0 ? "+" : ""}{s.change_pct?.toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
