"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchStockDetail, analyzeStock } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { useState } from "react";
import KlineChart from "@/components/KlineChart";

export default function StockWorkspace() {
  const { currentStock } = useAppStore();
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);

  const { data: stockData } = useQuery({
    queryKey: ["stock", currentStock],
    queryFn: () => fetchStockDetail(currentStock),
    enabled: !!currentStock,
  });

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const result = await analyzeStock(currentStock);
      setAnalysis(result);
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">{currentStock}</h2>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {analyzing ? "分析中..." : "AI 分析"}
        </button>
      </div>

      <div className="border rounded-lg p-4 dark:border-gray-800">
        <h3 className="font-semibold mb-2">K 线图</h3>
        <KlineChart data={[]} />
        <p className="text-sm text-gray-500 mt-2">
          后端提供行情数据后自动加载 K 线图。
        </p>
      </div>

      {stockData && (
        <div className="border rounded-lg p-4 dark:border-gray-800">
          <h3 className="font-semibold mb-2">股票信息</h3>
          <pre className="text-sm whitespace-pre-wrap">
            {JSON.stringify(stockData, null, 2)}
          </pre>
        </div>
      )}

      {analysis && (
        <div className="border rounded-lg p-4 dark:border-gray-800">
          <h3 className="font-semibold mb-2">AI 分析结果</h3>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-sm text-gray-500">决策</div>
              <div className="text-2xl font-bold uppercase">{analysis.decision}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">评分</div>
              <div className="text-2xl font-bold">
                {analysis.report?.overall_score ?? "N/A"}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">参与 Agent</div>
              <div className="text-2xl font-bold">
                {analysis.report?.agents_used?.length ?? 0}
              </div>
            </div>
          </div>
          {analysis.report?.key_points?.length > 0 && (
            <div>
              <h4 className="font-medium text-sm mb-1">关键发现</h4>
              <ul className="list-disc list-inside text-sm space-y-1">
                {analysis.report.key_points.map((p: string, i: number) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          )}
          {analysis.report?.warnings?.length > 0 && (
            <div className="mt-2">
              <h4 className="font-medium text-sm mb-1 text-yellow-600">风险提示</h4>
              <ul className="list-disc list-inside text-sm space-y-1 text-yellow-600">
                {analysis.report.warnings.map((w: string, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
