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
    <aside className="w-64 bg-iron-bg border-r border-iron-border flex flex-col shrink-0 min-h-screen z-20">
      {/* Brand Header */}
      <div className="p-5 border-b border-iron-border flex items-center justify-between">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-8 h-8 rounded-lg bg-iron-panel border border-iron-border flex items-center justify-center font-bold text-iron-accentPrimary shadow-sm group-hover:border-iron-accentPrimary transition-colors">
            <ShieldCheck className="w-4 h-4 text-iron-accentPrimary" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-iron-textPrimary font-sans">
              IronMind
            </h1>
            <p className="text-[11px] text-iron-textSecondary font-medium">Sovereign AI Workbench</p>
          </div>
        </Link>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navigationItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? "bg-iron-panel text-iron-textPrimary border border-iron-border border-l-2 border-l-iron-accentPrimary shadow-sm"
                  : "text-iron-textSecondary hover:text-iron-textPrimary hover:bg-iron-panel/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? "text-iron-accentPrimary" : "text-iron-textSecondary group-hover:text-iron-textPrimary"
                  }`}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-iron-panelSecondary text-iron-accentPrimary border border-iron-border">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Subtle Sovereignty Label at Bottom */}
      <div className="p-4 border-t border-iron-border">
        <div className="flex items-center justify-between text-[11px] text-iron-textSecondary font-mono">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-iron-success" />
            100% On-Premise
          </span>
          <span className="text-[10px]">v1.0</span>
        </div>
      </div>
    </aside>
  );
};
