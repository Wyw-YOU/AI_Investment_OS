"use client";

import { useState } from "react";
import { useAppStore } from "@/stores/appStore";

export default function StockInput() {
  const { currentStock, setCurrentStock } = useAppStore();
  const [value, setValue] = useState(currentStock);

  return (
    <div className="flex gap-1">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && setCurrentStock(value)}
        placeholder="Stock code"
        className="w-24 px-2 py-1 text-sm border rounded dark:bg-gray-900 dark:border-gray-700"
      />
      <button
        onClick={() => setCurrentStock(value)}
        className="px-2 py-1 text-sm bg-gray-200 dark:bg-gray-700 rounded"
      >
        Go
      </button>
    </div>
  );
}
