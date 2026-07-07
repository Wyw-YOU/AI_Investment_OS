"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { fetchWorkspaceDetail, fetchWorkspaceTimeline } from "@/lib/api";
import type { ApiResponse, Workspace, TimelineEvent } from "@/lib/types";

const RECOMMENDATION_COLORS: Record<string, string> = {
  strong_buy: "text-green-300 bg-green-900/40",
  buy: "text-green-400 bg-green-900/30",
  hold: "text-yellow-400 bg-yellow-900/30",
  sell: "text-red-400 bg-red-900/30",
  strong_sell: "text-red-300 bg-red-900/40",
};

export default function WorkspaceDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const wsId = parseInt(id);
    Promise.all([
      fetchWorkspaceDetail(wsId),
      fetchWorkspaceTimeline(wsId),
    ])
      .then(([wsResp, tlResp]) => {
        setWorkspace((wsResp as ApiResponse<Workspace>).data);
        setTimeline((tlResp as ApiResponse<TimelineEvent[]>).data || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        {loading ? (
          <p className="text-slate-500">加载中...</p>
        ) : !workspace ? (
          <p className="text-red-400">研究空间未找到</p>
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-white">{workspace.name}</h1>
                <p className="text-slate-500 text-sm">
                  {workspace.stock_code} · 创建于 {new Date(workspace.created_at).toLocaleDateString("zh-CN")}
                </p>
              </div>
              <a
                href={`/stock/${workspace.stock_code}`}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm"
              >
                进入分析
              </a>
            </div>

            {/* Timeline */}
            <div className="bg-slate-800/50 rounded-xl p-4">
              <h3 className="text-sm font-medium text-blue-400 mb-4">  研究时间线</h3>
              {timeline.length === 0 ? (
                <p className="text-slate-500 text-sm">暂无记录</p>
              ) : (
                <div className="space-y-3">
                  {timeline.map((event, i) => (
                    <div key={i} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-3 h-3 rounded-full ${event.type === "analysis" ? "bg-blue-500" : "bg-yellow-500"}`} />
                        {i < timeline.length - 1 && <div className="w-px flex-1 bg-slate-700 mt-1" />}
                      </div>
                      <div className="pb-4 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs px-2 py-0.5 rounded ${event.type === "analysis" ? "bg-blue-900/40 text-blue-400" : "bg-yellow-900/40 text-yellow-400"}`}>
                            {event.type === "analysis" ? "AI 分析" : "笔记"}
                          </span>
                          <span className="text-slate-600 text-xs">
                            {new Date(event.created_at).toLocaleString("zh-CN")}
                          </span>
                        </div>
                        {event.type === "analysis" && event.recommendation && (
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium mb-1 ${RECOMMENDATION_COLORS[event.recommendation] || "text-slate-400"}`}>
                            {event.recommendation.toUpperCase()} {event.score ? `(${event.score}/100)` : ""}
                          </span>
                        )}
                        <p className="text-sm text-slate-300">
                          {event.type === "analysis" ? event.summary : event.content}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
