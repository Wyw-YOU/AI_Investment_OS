"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { analyzeStock } from "@/lib/api";

export default function AnalyzePanel() {
  const [code, setCode] = useState("600519");
  const mutation = useMutation({ mutationFn: analyzeStock });

  return (
    <div className="border rounded-lg p-4 dark:border-gray-800">
      <h2 className="font-semibold mb-3">AI Analysis</h2>
      <div className="flex gap-2">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Stock code"
          className="flex-1 px-3 py-2 border rounded dark:bg-gray-900 dark:border-gray-700"
        />
        <button
          onClick={() => mutation.mutate(code)}
          disabled={mutation.isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {mutation.isPending ? "Analyzing..." : "Analyze"}
        </button>
      </div>
      {mutation.data && (
        <div className="mt-3 text-sm p-3 bg-gray-50 dark:bg-gray-800 rounded">
          <pre className="whitespace-pre-wrap">{JSON.stringify(mutation.data, null, 2)}</pre>
        </div>
      )}
      {mutation.error && (
        <p className="mt-2 text-sm text-red-600">Error: {(mutation.error as Error).message}</p>
      )}
    </div>
  );
}
