"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { fetchWorkspaces } from "@/lib/api";
import type { ApiResponse, Workspace } from "@/lib/types";

export default function WorkspacePage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWorkspaces()
      .then((r: ApiResponse<Workspace[]>) => setWorkspaces(r.data || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">  研究空间</h1>
        </div>

        {loading ? (
          <p className="text-slate-500">加载中...</p>
        ) : workspaces.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-slate-500 text-lg">暂无研究空间</p>
            <p className="text-slate-600 text-sm mt-2">对股票进行 AI 分析后，系统会自动创建研究空间</p>
            <a href="/stock/600519" className="inline-block mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm">
              开始分析
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workspaces.map((ws) => (
              <a
                key={ws.id}
                href={`/workspace/${ws.id}`}
                className="bg-slate-800/50 hover:bg-slate-800 rounded-xl p-5 border border-slate-700/50 transition-colors group"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-white font-medium group-hover:text-blue-400 transition-colors">{ws.name}</h3>
                  <span className="text-slate-500 text-xs font-mono">{ws.stock_code}</span>
                </div>
                <p className="text-slate-500 text-xs">
                  创建于 {new Date(ws.created_at).toLocaleDateString("zh-CN")}
                </p>
              </a>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
