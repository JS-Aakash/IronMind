import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4">
      <h2 className="text-2xl font-bold text-iron-textPrimary">404 - Page Not Found</h2>
      <p className="text-sm text-iron-textSecondary">The requested route does not exist in IronMind sovereign platform.</p>
      <Link
        href="/workbench"
        className="px-4 py-2 rounded-lg bg-iron-accentPrimary hover:bg-iron-accentPrimary/90 text-white text-xs font-mono font-bold transition"
      >
        Return to Workbench
      </Link>
    </div>
  );
}
