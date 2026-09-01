"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import { ArtifactItem } from "@/lib/types";
import {
  FileCheck2,
  Download,
  ShieldCheck,
  FileText,
  CheckCircle2,
  RefreshCw,
  Copy,
  Check,
  Clock,
  Sparkles,
  FileCode,
  FileType,
} from "lucide-react";

export default function ArtifactsPage() {
  const [artifacts, setArtifacts] = useState<ArtifactItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const loadArtifacts = async () => {
    try {
      setLoading(true);
      const data = await api.getArtifacts();
      setArtifacts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadArtifacts();
  }, []);

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleGenerateSampleApproval = async () => {
    try {
      setLoading(true);
      await api.generateApprovalNote({
        subject: "Approval for Overhaul of Slurry Pump P-101 (CDU-1)",
        equipment_tag: "P-101",
      });
      await loadArtifacts();
    } catch (e) {
      console.error("Failed to generate deliverable:", e);
    } finally {
      setLoading(false);
    }
  };

  const getDeliverableIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase();
    if (["docx", "doc"].includes(ext || "")) {
      return <FileType className="w-5 h-5 text-indigo-400" />;
    }
    if (["pdf"].includes(ext || "")) {
      return <FileText className="w-5 h-5 text-rose-400" />;
    }
    if (["py"].includes(ext || "")) {
      return <FileCode className="w-5 h-5 text-cyan-400" />;
    }
    return <FileCheck2 className="w-5 h-5 text-emerald-400" />;
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileCheck2 className="w-6 h-6 text-emerald-400" />
            <span>Generated Business Deliverables</span>
          </h2>
          <p className="text-xs md:text-sm text-slate-400">
            Real Microsoft Word (.docx), Python (.py), and Excel (.xlsx) deliverables with SHA-256 cryptographic provenance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleGenerateSampleApproval}
            className="shimmer-button flex items-center gap-2 px-4 py-2 rounded-xl text-white font-semibold text-xs transition cursor-pointer shadow-lg shadow-indigo-500/25"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Create Approval DOCX</span>
          </button>
          <button
            onClick={loadArtifacts}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.09] text-slate-200 text-xs font-semibold transition border border-white/10"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Artifacts List */}
      <div className="space-y-3.5">
        {artifacts.length === 0 ? (
          <div className="p-16 text-center rounded-3xl glass-panel space-y-3">
            <FileCheck2 className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-sm font-semibold text-slate-300">No deliverables generated yet</div>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Run an approval note or coding task in the Workbench to generate deliverables with cryptographic proofs.
            </p>
          </div>
        ) : (
          artifacts.map((art) => {
            const downloadHref = `http://127.0.0.1:8000/api/v1/artifacts/${art.artifact_id}/download`;
            const sizeKb = art.size_bytes ? (art.size_bytes / 1024).toFixed(1) : "0";

            return (
              <div
                key={art.artifact_id}
                className="glass-panel-interactive p-5 rounded-3xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 rounded-2xl bg-obsidian-950/90 border border-white/10 flex items-center justify-center">
                    {getDeliverableIcon(art.filename)}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <span className="font-bold text-sm text-slate-100">{art.filename}</span>
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 uppercase">
                        {art.type || "Deliverable"}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono">
                      <span>ID: {art.artifact_id}</span>
                      <span>•</span>
                      <span>{sizeKb} KB</span>
                      {art.created_at && (
                        <>
                          <span>•</span>
                          <span>{new Date(art.created_at).toLocaleTimeString()}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full md:w-auto justify-end pt-2 md:pt-0 border-t md:border-t-0 border-white/5">
                  {art.sha256_hash && (
                    <button
                      onClick={() => handleCopyHash(art.sha256_hash)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-obsidian-950/80 border border-white/10 text-slate-300 hover:text-white text-xs font-mono transition"
                      title="Copy SHA-256 Hash"
                    >
                      {copiedHash === art.sha256_hash ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5 text-slate-400" />
                      )}
                      <span>{art.sha256_hash.substring(0, 10)}...</span>
                    </button>
                  )}

                  <a
                    href={downloadHref}
                    download
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition shadow-md shadow-emerald-500/20"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </a>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
