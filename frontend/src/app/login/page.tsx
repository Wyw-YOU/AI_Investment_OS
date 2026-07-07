"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const fn = isRegister ? register : login;
      const resp = await fn(email, password);
      if (resp.data?.token) {
        localStorage.setItem("token", resp.data.token);
        router.push("/");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Operation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="w-full max-w-md p-8 bg-slate-900 rounded-2xl border border-slate-800">
        <h1 className="text-2xl font-bold text-white text-center mb-1">AI Investment OS</h1>
        <p className="text-slate-500 text-center text-sm mb-4">
          Multi-Agent 投资研究操作系统
        </p>

        {/* Login / Register Tab Buttons */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setIsRegister(false)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${!isRegister ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-slate-200"}`}
          >
            登录
          </button>
          <button
            onClick={() => setIsRegister(true)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${isRegister ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:text-slate-200"}`}
          >
            注册
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-slate-400 mb-1 block">邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              placeholder="your@email.com"
            />
          </div>
          <div>
            <label className="text-sm text-slate-400 mb-1 block">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              placeholder="******"
            />
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg text-white font-medium transition-colors"
          >
            {loading ? "..." : isRegister ? "注册" : "登录"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500 mt-4">
          {isRegister ? "已有账户?" : "没有账户?"}{" "}
          <button onClick={() => setIsRegister(!isRegister)} className="text-blue-400 hover:underline">
            {isRegister ? "登录" : "注册"}
          </button>
        </p>
      </div>
    </div>
  );
}
