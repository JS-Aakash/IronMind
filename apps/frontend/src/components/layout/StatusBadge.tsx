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
        return "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
      case "standby":
      case "pending":
      case "classifying":
      case "planning":
        return "bg-amber-500/15 text-amber-300 border-amber-500/30";
      case "executing":
      case "verifying":
      case "processing":
        return "bg-palette-royal/30 text-palette-periwinkle border-palette-periwinkle/40 animate-pulse";
      case "failed":
      case "error":
      case "breach":
        return "bg-rose-500/15 text-rose-300 border-rose-500/30";
      default:
        return "bg-palette-violet/30 text-palette-ice border-palette-periwinkle/20";
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
