"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { fetchWorkspaces, createWorkspace } from "@/lib/api";
import type { ApiResponse, Workspace } from "@/lib/types";

export default function PortfolioPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [newCode, setNewCode] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const resp = (await fetchWorkspaces()) as ApiResponse<Workspace[]>;
      setWorkspaces(resp.data || []);
    } catch {
      // not logged in or error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!newCode.trim()) return;
    try {
      await createWorkspace(newCode.trim());
      setNewCode("");
      load();
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6">
        <h1 className="text-2xl font-bold text-white mb-6">Portfolio</h1>

        {/* Create workspace */}
        <div className="bg-slate-800/50 rounded-xl p-4 mb-6 flex gap-3">
          <input
            type="text"
            value={newCode}
            onChange={(e) => setNewCode(e.target.value)}
            placeholder="输入股票代码添加到研究空间"
            className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <button
            onClick={handleCreate}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-medium"
          >
            添加
          </button>
        </div>

        {/* Workspace list */}
        {loading ? (
          <p className="text-slate-500">加载中...</p>
        ) : workspaces.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-slate-500">暂无研究空间</p>
            <p className="text-slate-600 text-sm mt-2">输入股票代码创建第一个研究空间</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {workspaces.map((ws) => (
              <a
                key={ws.id}
                href={`/stock/${ws.stock_code}`}
                className="bg-slate-800/50 hover:bg-slate-800 rounded-xl p-4 border border-slate-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-medium">{ws.name}</h3>
                  <span className="text-slate-500 text-xs">{ws.stock_code}</span>
                </div>
                <p className="text-slate-500 text-xs mt-2">
                  Created: {new Date(ws.created_at).toLocaleDateString("zh-CN")}
                </p>
              </a>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
