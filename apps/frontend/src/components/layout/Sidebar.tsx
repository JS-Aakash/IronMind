"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Cpu,
  Bot,
  BookOpen,
  Boxes,
  FileCheck2,
  ShieldCheck,
  ScrollText,
  Sparkles,
  Zap,
} from "lucide-react";

const navigationItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Workbench", href: "/workbench", icon: Cpu, badge: "AI" },
  { name: "Agent Execution", href: "/runs", icon: Bot },
  { name: "Knowledge Base", href: "/knowledge", icon: BookOpen },
  { name: "Model Gateway", href: "/models", icon: Boxes },
  { name: "Deliverables", href: "/artifacts", icon: FileCheck2 },
  { name: "Security & Trust", href: "/sovereignty", icon: ShieldCheck },
  { name: "Audit Trail", href: "/audit", icon: ScrollText },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-obsidian-950/90 border-r border-white/5 flex flex-col shrink-0 min-h-screen backdrop-blur-xl z-20">
      {/* Brand Header */}
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-base tracking-tight text-white flex items-center gap-1.5 font-sans">
              IronMind
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">Enterprise Agent Workbench</p>
          </div>
        </Link>
      </div>

      {/* Quick Status / Engine Card */}
      <div className="mx-4 my-3 p-3 rounded-xl bg-obsidian-900/80 border border-white/5 flex items-center justify-between shadow-inner">
        <div className="flex items-center space-x-2.5">
          <div className="w-2 h-2 rounded-full bg-emerald-400 pulse-dot" />
          <div>
            <div className="text-xs font-semibold text-slate-200">Local Engine Active</div>
            <div className="text-[10px] text-slate-400">Autonomous Orchestrator</div>
          </div>
        </div>
        <div className="p-1 rounded-md bg-indigo-500/10 text-indigo-400">
          <Zap className="w-3.5 h-3.5" />
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-2 space-y-1">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                isActive
                  ? "bg-gradient-to-r from-indigo-500/15 to-indigo-500/5 text-indigo-300 border border-indigo-500/25 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? "text-indigo-400" : "text-slate-400 group-hover:text-slate-200"
                  }`}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer info */}
      <div className="p-4 border-t border-white/5 text-xs text-slate-400">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-400">IronMind Platform</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-slate-300 font-mono">
            v2.4.0
          </span>
        </div>
      </div>
    </aside>
  );
};
