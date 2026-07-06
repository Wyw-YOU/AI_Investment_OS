"use client";

import { useState } from "react";
import { runAnalysis } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

interface Props {
  stockCode: string;
}

const RECOMMENDATION_COLORS: Record<string, string> = {
  strong_buy: "text-green-300 bg-green-900/50",
  buy: "text-green-400 bg-green-900/30",
  hold: "text-yellow-400 bg-yellow-900/30",
  sell: "text-red-400 bg-red-900/30",
  strong_sell: "text-red-300 bg-red-900/50",
};

export default function AnalyzePanel({ stockCode }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const resp = await runAnalysis(stockCode);
      setResult(resp.data as AnalysisResult);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg text-white font-medium transition-colors"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            AI 分析中...
          </span>
        ) : (
          "开始 AI 分析"
        )}
      </button>

      {error && (
        <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">{error}</div>
      )}

      {result && (
        <div className="space-y-3">
          {/* Final Report */}
          {result.final_report?.executive_summary && (
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-blue-400 mb-2">  投资报告</h3>
              <p className="text-sm text-slate-300 mb-3">{result.final_report.executive_summary}</p>
              {result.final_report.recommendation && (
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${RECOMMENDATION_COLORS[result.final_report.recommendation] || "text-slate-400"}`}>
                  {result.final_report.recommendation.toUpperCase()}
                </span>
              )}
              {result.final_report.overall_score !== undefined && (
                <span className="ml-3 text-sm text-slate-400">评分: {result.final_report.overall_score}/100</span>
              )}
            </div>
          )}

          {/* Key Findings */}
          {result.final_report?.key_findings && result.final_report.key_findings.length > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-yellow-400 mb-2">  核心发现</h3>
              <ul className="space-y-1">
                {result.final_report.key_findings.map((f: string, i: number) => (
                  <li key={i} className="text-sm text-slate-300 flex gap-2">
                    <span className="text-yellow-500">•</span> {f}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risk */}
          {result.risk_assessment && (
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-red-400 mb-2">  风险评估</h3>
              <div className="flex gap-4 text-sm">
                <span className="text-slate-400">风险等级: <span className="text-white">{result.risk_assessment.overall_risk || "N/A"}</span></span>
                <span className="text-slate-400">风险分: <span className="text-white">{result.risk_assessment.risk_score ?? "N/A"}</span></span>
              </div>
            </div>
          )}

          {/* Agent Confidence */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <h3 className="text-sm font-medium text-purple-400 mb-2">  Agent 置信度</h3>
            <div className="space-y-1.5">
              {Object.entries(result.agent_outputs).map(([name, info]) => (
                <div key={name} className="flex items-center gap-2 text-sm">
                  <span className="w-20 text-slate-400">{name}</span>
                  <div className="flex-1 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(info.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-slate-300 w-10 text-right">{((info.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
