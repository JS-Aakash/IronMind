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
  ChevronRight,
  Radio,
  Lock,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  badge?: string;
  badgeType?: "sky" | "emerald" | "indigo" | "slate";
}

interface NavGroup {
  category: string;
  items: NavItem[];
}

const navigationGroups: NavGroup[] = [
  {
    category: "OPERATIONS",
    items: [
      { name: "Overview", href: "/", icon: LayoutDashboard },
      { name: "Workbench", href: "/workbench", icon: Cpu },
      { name: "Agent Execution", href: "/runs", icon: Bot },
    ],
  },
  {
    category: "INTELLIGENCE & ASSETS",
    items: [
      { name: "Knowledge Base", href: "/knowledge", icon: BookOpen, badge: "8 Docs", badgeType: "slate" },
      { name: "Model Gateway", href: "/models", icon: Boxes, badge: "4 Local", badgeType: "indigo" },
      { name: "Deliverables", href: "/artifacts", icon: FileCheck2 },
    ],
  },
  {
    category: "GOVERNANCE",
    items: [
      { name: "Security & Trust", href: "/sovereignty", icon: ShieldCheck },
      { name: "Audit Trail", href: "/audit", icon: ScrollText },
    ],
  },
];

export const Sidebar = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#070B14] border-r border-slate-800/80 flex flex-col shrink-0 min-h-screen z-20 shadow-2xl select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800/70">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500/20 via-slate-800 to-indigo-500/20 border border-sky-500/40 flex items-center justify-center font-bold text-sky-400 shadow-[0_0_12px_rgba(14,165,233,0.25)] group-hover:border-sky-400 transition-all">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <h1 className="font-extrabold text-sm tracking-wide text-white font-sans">
                IronMind
              </h1>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-500/15 text-sky-300 border border-sky-500/30 font-bold">
                SOVEREIGN
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono truncate">
              Industrial AI Workbench
            </p>
          </div>
        </Link>
      </div>

      {/* Grouped Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {navigationGroups.map((group) => (
          <div key={group.category} className="space-y-1">
            <div className="px-3 pb-1 flex items-center justify-between text-[10px] font-mono font-bold tracking-wider text-slate-500 uppercase">
              <span>{group.category}</span>
            </div>
            <div className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-medium transition-all group ${
                      isActive
                        ? "bg-gradient-to-r from-sky-500/15 via-sky-500/5 to-transparent text-white border border-sky-500/30 border-l-2 border-l-sky-400 shadow-sm"
                        : "text-slate-400 hover:text-white hover:bg-slate-800/40"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          isActive
                            ? "text-sky-400"
                            : "text-slate-500 group-hover:text-sky-300"
                        }`}
                      />
                      <span className="tracking-tight truncate">{item.name}</span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.badge && (
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold transition-colors ${
                            item.badgeType === "emerald"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : item.badgeType === "indigo"
                              ? "bg-indigo-500/15 text-indigo-300 border border-indigo-500/30"
                              : item.badgeType === "sky"
                              ? "bg-sky-500/15 text-sky-300 border border-sky-500/30"
                              : "bg-slate-800 text-slate-400 border border-slate-700/60"
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-sky-400 shadow-[0_0_6px_rgba(56,189,248,0.8)]" />
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
};
