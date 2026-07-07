"use client";

/**
 * AI 分析面板：发起分析、展示实时进度、呈现最终报告。
 *
 * 双通道进度获取：
 * 1. WebSocket（主通道）：后端 agent 每次状态变化实时推送
 * 2. 轮询（降级通道）：每 3 秒 GET /status，防止 WebSocket 断连后进度停滞
 *
 * WebSocket 断连或 report agent 完成后，轮询自动停止。
 */

import { useEffect, useRef, useState } from "react";
import { startAnalysis, getAnalysisStatus, connectAnalysisWS } from "@/lib/api";
import type { AnalysisResult, AnalysisProgressEvent } from "@/lib/types";

interface Props {
  stockCode: string;
}

const AGENTS = ["planner", "news", "financial", "technical", "macro", "risk", "quant", "report"] as const;
const AGENT_LABELS: Record<string, string> = {
  planner: "任务规划",
  news: "新闻分析",
  financial: "基本面",
  technical: "技术分析",
  macro: "宏观分析",
  risk: "风险评估",
  quant: "量化评分",
  report: "生成报告",
};

const RECOMMENDATION_COLORS: Record<string, string> = {
  strong_buy: "text-green-300 bg-green-900/50",
  buy: "text-green-400 bg-green-900/30",
  hold: "text-yellow-400 bg-yellow-900/30",
  sell: "text-red-400 bg-red-900/30",
  strong_sell: "text-red-300 bg-red-900/50",
};

type AnalysisStatus = "idle" | "running" | "done" | "error";

function AgentStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <span className="text-green-400">  </span>;
  if (status === "started") return <span className="text-blue-400 animate-pulse">  </span>;
  if (status === "failed") return <span className="text-red-400">  </span>;
  return <span className="text-slate-600"> </span>;
}

export default function AnalyzePanel({ stockCode }: Props) {
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [agentProgress, setAgentProgress] = useState<Record<string, string>>({});
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem("token"));
    return () => {
      wsRef.current?.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleAnalyze = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setError("请先登录后再使用 AI 分析功能");
      setStatus("error");
      setIsLoggedIn(false);
      return;
    }
    setStatus("running");
    setResult(null);
    setError("");
    setAgentProgress(Object.fromEntries(AGENTS.map((a) => [a, "pending"])));

    try {
      const resp = await startAnalysis(stockCode);
      const data = resp.data;
      const taskId: number = data.task_id;
      const analysisId: string = data.analysis_id;

      // Connect WebSocket for real-time progress
      wsRef.current = connectAnalysisWS(analysisId, (event: AnalysisProgressEvent) => {
        setAgentProgress((prev) => ({ ...prev, [event.agent_name]: event.status }));
        if (event.agent_name === "report" && event.status === "completed") {
          fetchResult(taskId);
        }
        if (event.agent_name === "report" && event.status === "failed") {
          setError("报告生成失败");
          setStatus("error");
        }
      });

      // Fallback polling every 3s
      pollRef.current = setInterval(async () => {
        try {
          const r = await getAnalysisStatus(taskId);
          const d = r.data;
          if (d.progress) {
            setAgentProgress((prev) => ({ ...prev, ...d.progress }));
          }
          if (d.status === "complete" || d.status === "failed") {
            cleanup();
            if (d.status === "complete") {
              setResult(d as AnalysisResult);
              setStatus("done");
            } else {
              setError(d.error_message || "分析失败");
              setStatus("error");
            }
          }
        } catch {}
      }, 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "启动分析失败");
      setStatus("error");
    }
  };

  const fetchResult = async (taskId: number) => {
    cleanup();
    try {
      const r = await getAnalysisStatus(taskId);
      setResult(r.data as AnalysisResult);
      setStatus("done");
    } catch {
      setError("获取结果失败");
      setStatus("error");
    }
  };

  const cleanup = () => {
    wsRef.current?.close();
    wsRef.current = null;
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Action button */}
      {status === "idle" || status === "done" || status === "error" ? (
        <button
          onClick={handleAnalyze}
          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
        >
          {status === "done" ? "  重新分析" : "  开始 AI 分析"}
        </button>
      ) : null}

      {error && status === "error" && (
        <div className="p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-400 text-sm">
          {error}
          {!isLoggedIn && (
            <a href="/login" className="ml-2 underline text-blue-400 hover:text-blue-300">去登录</a>
          )}
        </div>
      )}

      {/* Running: per-agent progress */}
      {status === "running" && (
        <div className="bg-slate-800/50 rounded-xl p-4">
          <h3 className="text-sm font-medium text-blue-400 mb-3">  Agent 分析进度</h3>
          <div className="space-y-2">
            {AGENTS.map((name) => (
              <div key={name} className="flex items-center gap-3 text-sm">
                <AgentStatusIcon status={agentProgress[name] || "pending"} />
                <span className="w-20 text-slate-400">{AGENT_LABELS[name]}</span>
                <div className="flex-1 bg-slate-700 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-500 ${
                      agentProgress[name] === "completed"
                        ? "bg-green-500 w-full"
                        : agentProgress[name] === "started"
                          ? "bg-blue-500 w-2/3 animate-pulse"
                          : agentProgress[name] === "failed"
                            ? "bg-red-500 w-full"
                            : "bg-slate-600 w-0"
                    }`}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {result && status === "done" && (
        <div className="space-y-3">
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

          {result.risk_assessment && (
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-red-400 mb-2">  风险评估</h3>
              <div className="flex gap-4 text-sm">
                <span className="text-slate-400">风险等级: <span className="text-white">{result.risk_assessment.overall_risk || "N/A"}</span></span>
                <span className="text-slate-400">风险分: <span className="text-white">{result.risk_assessment.risk_score ?? "N/A"}</span></span>
              </div>
            </div>
          )}

          <div className="bg-slate-800/50 rounded-xl p-4">
            <h3 className="text-sm font-medium text-purple-400 mb-2">  Agent 置信度</h3>
            <div className="space-y-1.5">
              {Object.entries(result.agent_outputs || {}).map(([name, info]) => (
                <div key={name} className="flex items-center gap-2 text-sm">
                  <span className="w-20 text-slate-400">{AGENT_LABELS[name] || name}</span>
                  <div className="flex-1 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${((info as { confidence?: number })?.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-slate-300 w-10 text-right">{(((info as { confidence?: number })?.confidence || 0) * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
