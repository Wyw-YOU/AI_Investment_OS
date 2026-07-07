"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: " " },
  { href: "/workspace", label: "研究空间", icon: " " },
  { href: "/stock/600519", label: "个股分析", icon: " " },
  { href: "/portfolio", label: "Portfolio", icon: " " },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-slate-900 border-r border-slate-800 min-h-screen p-4 relative">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-blue-400">AI Investment OS</h1>
        <p className="text-xs text-slate-500 mt-1">Multi-Agent Research System</p>
      </div>
      <nav className="space-y-1">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
                ? "bg-blue-600/20 text-blue-400"
                : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="absolute bottom-4 left-4 right-4 space-y-1">
        <Link
          href="/login"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
        >
          <span> </span><span>登录 / 注册</span>
        </Link>
      </div>
    </aside>
  );
}
