"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchUnreadAlerts } from "@/lib/api";

export default function NotificationBell() {
  const { data } = useQuery({
    queryKey: ["unread-alerts"],
    queryFn: () => fetchUnreadAlerts(),
    refetchInterval: 30_000,
  });

  const count = data?.count ?? 0;

  return (
    <div className="relative">
      <span className="text-xl">🔔</span>
      {count > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
          {count > 9 ? "9+" : count}
        </span>
      )}
    </div>
  );
}
