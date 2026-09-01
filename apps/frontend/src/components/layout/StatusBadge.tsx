import React from "react";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = "" }) => {
  const normalized = status?.toLowerCase() || "unknown";

  const getStyle = () => {
    switch (normalized) {
      case "healthy":
      case "active":
      case "loaded":
      case "ready":
      case "completed":
      case "verified":
      case "verified_local":
        return "bg-emerald-500/10 text-emerald-300 border-emerald-500/25";
      case "standby":
      case "pending":
      case "classifying":
      case "planning":
        return "bg-amber-500/10 text-amber-300 border-amber-500/25";
      case "executing":
      case "verifying":
      case "processing":
        return "bg-indigo-500/15 text-indigo-300 border-indigo-500/30 animate-pulse";
      case "failed":
      case "error":
      case "breach":
        return "bg-rose-500/10 text-rose-300 border-rose-500/25";
      default:
        return "bg-slate-800/80 text-slate-300 border-white/10";
    }
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-[11px] font-mono font-medium rounded-full border tracking-wide shadow-sm ${getStyle()} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
};
