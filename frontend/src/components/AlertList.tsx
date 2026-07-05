"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchAlerts, Alert } from "@/lib/api";

export default function AlertList() {
  const { data, isLoading } = useQuery({
    queryKey: ["alerts"],
    queryFn: () => fetchAlerts(),
  });

  if (isLoading) return <div className="animate-pulse h-40 bg-gray-100 dark:bg-gray-800 rounded" />;

  const alerts = data?.alerts ?? [];

  return (
    <div className="border rounded-lg p-4 dark:border-gray-800">
      <h2 className="font-semibold mb-3">Alerts</h2>
      {alerts.length === 0 ? (
        <p className="text-sm text-gray-500">No alerts.</p>
      ) : (
        <div className="space-y-2">
          {alerts.slice(0, 10).map((a: Alert) => (
            <div key={a.id} className="text-sm p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
              <span className="font-medium">{a.stock_code}</span>: {a.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
