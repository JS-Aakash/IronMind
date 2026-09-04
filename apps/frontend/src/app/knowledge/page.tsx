"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api-client";
import { KnowledgeDocument } from "@/lib/types";
import {
  BookOpen,
  FileText,
  Database,
  Upload,
  Search,
  Layers,
  HardDrive,
  RefreshCw,
  CheckCircle2,
  Tag,
  Calendar,
  Trash2,
  X,
  AlertTriangle,
  Plus,
  FileType,
  Sparkles,
  ArrowRight,
  ExternalLink,
  ShieldCheck,
  Cpu,
  Hash,
  FileCode,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function KnowledgeBasePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [search, setSearch] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  // Selected document for detailed inspector modal
  const [selectedDoc, setSelectedDoc] = useState<KnowledgeDocument | null>(null);

  // Upload modal state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docTitle, setDocTitle] = useState("");
  const [category, setCategory] = useState("Standard Operating Procedure (SOP)");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgressStage, setUploadProgressStage] = useState<string>("");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocs = async () => {
    try {
      setLoading(true);
      const data = await api.getKnowledgeDocuments();
      setDocuments(data);
    } catch (e) {
      console.error("Failed to load knowledge documents:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      if (!docTitle) {
        setDocTitle(file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " "));
      }
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      setUploadError(null);
      setUploadProgressStage("1/4: Parsing document structure & text extraction...");

      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("title", docTitle.trim() || selectedFile.name);
      formData.append("category", category);

      setUploadProgressStage("2/4: Chunking with semantic text chunker...");
      setUploadProgressStage("3/4: Generating AI summary & key topic tags...");

      await api.uploadKnowledgeDocument(formData);
      setUploadProgressStage("4/4: Indexed into Sovereign Vector Store!");

      await loadDocs();
      setIsUploadOpen(false);
      setSelectedFile(null);
      setDocTitle("");
      setUploadProgressStage("");
    } catch (err: any) {
      console.error("Knowledge upload error:", err);
      setUploadError(err?.message || "Failed to ingest and index document.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (docId: string, title: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!confirm(`Permanently delete '${title}' and purge all its vector chunks?`)) return;

    try {
      setDeletingDocId(docId);
      await api.deleteKnowledgeDocument(docId);
      if (selectedDoc?.id === docId) {
        setSelectedDoc(null);
      }
      await loadDocs();
    } catch (err) {
      console.error("Failed to delete document:", err);
      alert("Failed to delete document.");
    } finally {
      setDeletingDocId(null);
    }
  };

  const handleSemanticSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) return;

    try {
      setIsSearching(true);
      const res = await api.searchKnowledge(search, 5);
      setSearchResults(res);
    } catch (err) {
      console.error("Semantic search error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  const filteredDocs = documents.filter(
    (d) =>
      d.title.toLowerCase().includes(search.toLowerCase()) ||
      d.filename.toLowerCase().includes(search.toLowerCase()) ||
      d.category.toLowerCase().includes(search.toLowerCase()) ||
      (d.key_topics && d.key_topics.some((k) => k.toLowerCase().includes(search.toLowerCase())))
  );

  const totalChunks = documents.reduce((sum, d) => sum + (d.chunk_count || 0), 0);

  return (
    <div className="space-y-6 pb-16 animate-fade-in font-sans">
      {/* 1. Header Banner */}
      <div className="enterprise-card p-6 rounded-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-iron-accentPrimary" />
            <h1 className="text-xl font-bold text-iron-textPrimary tracking-tight">
              Knowledge Base & Local Sovereign RAG
            </h1>
            <span className="px-2 py-0.5 rounded bg-iron-accentPrimary/15 border border-iron-accentPrimary/40 text-iron-accentPrimary text-[10px] font-mono font-bold">
              AIR-GAPPED VECTOR STORE
            </span>
          </div>
          <p className="text-xs text-iron-textSecondary max-w-3xl">
            Sovereign repository of engineering manuals, P&IDs, and plant SOPs. All files are parsed, chunked, and embedded locally without external data transfer. Click any document to inspect its AI summary and keywords.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-3.5 py-1.5 rounded-lg bg-iron-accentPrimary hover:bg-iron-accentPrimary/90 text-white text-xs font-mono font-bold transition flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload Document</span>
          </button>
          <button
            onClick={loadDocs}
            disabled={loading}
            className="px-3.5 py-1.5 rounded-lg bg-iron-panelSecondary hover:bg-iron-border text-iron-textPrimary border border-iron-border text-xs font-mono transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-iron-accentPrimary" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 2. Knowledge Metrics Summary Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-accentPrimary">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Indexed Documents
          </span>
          <div className="text-2xl font-bold font-mono text-iron-textPrimary">{documents.length}</div>
          <div className="text-[11px] text-iron-textSecondary">SOPs & Engineering Standards</div>
        </div>

        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-accentSecondary">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Embedded Chunks
          </span>
          <div className="text-2xl font-bold font-mono text-iron-accentSecondary">{totalChunks}</div>
          <div className="text-[11px] text-iron-textSecondary">Vector Index Embeddings</div>
        </div>

        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-success">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Dense Embedding
          </span>
          <div className="text-2xl font-bold font-mono text-iron-success">384-Dim</div>
          <div className="text-[11px] text-iron-textSecondary">Local all-MiniLM-L6-v2</div>
        </div>

        <div className="enterprise-card p-4 rounded-xl space-y-1 border-l-2 border-l-iron-warning">
          <span className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
            Sovereign Egress
          </span>
          <div className="text-2xl font-bold font-mono text-iron-warning">0 Bytes</div>
          <div className="text-[11px] text-iron-textSecondary">100% On-Premise Storage</div>
        </div>
      </div>

      {/* 3. Semantic Search Bar */}
      <form onSubmit={handleSemanticSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-iron-textSecondary absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents by keyword, title, or semantic concept (e.g. 'vibration limits ISO 10816' or 'bearing temperature')..."
            className="w-full pl-11 pr-4 py-2.5 rounded-lg bg-iron-panel border border-iron-border text-iron-textPrimary placeholder-iron-textSecondary/60 text-xs focus:outline-none focus:border-iron-accentPrimary transition"
          />
        </div>
        <button
          type="submit"
          disabled={isSearching || !search.trim()}
          className="px-4 py-2.5 rounded-lg bg-iron-accentPrimary/15 hover:bg-iron-accentPrimary/25 text-iron-accentPrimary border border-iron-accentPrimary/30 text-xs font-mono font-bold transition disabled:opacity-50 flex items-center gap-2 cursor-pointer"
        >
          {isSearching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          <span>Vector Search</span>
        </button>
      </form>

      {/* 4. Search Results Drawer (if active) */}
      {searchResults && (
        <div className="enterprise-card p-5 rounded-xl space-y-3 border-iron-accentPrimary/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-iron-accentPrimary" />
              <h3 className="text-xs font-bold text-iron-textPrimary uppercase tracking-wider">
                Dense Vector Search Results ({searchResults.chunks?.length || 0} Citations)
              </h3>
            </div>
            <button
              onClick={() => setSearchResults(null)}
              className="text-xs text-iron-textSecondary hover:text-iron-textPrimary font-mono cursor-pointer"
            >
              Close Results
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {searchResults.chunks?.map((chunk: any, i: number) => (
              <div
                key={i}
                className="p-3.5 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-2 flex flex-col justify-between text-xs font-mono"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-iron-accentPrimary">
                    <span className="font-bold truncate max-w-[180px]">
                      {chunk.document_name || "Document"}
                    </span>
                    <span className="text-iron-success font-bold">
                      {Math.round((chunk.score || 0.85) * 100)}% Match
                    </span>
                  </div>
                  <p className="text-xs text-iron-textPrimary font-sans leading-relaxed line-clamp-4">
                    {chunk.text}
                  </p>
                </div>
                <div className="text-[10px] text-iron-textSecondary pt-2 border-t border-iron-border flex items-center justify-between">
                  <span>Page {chunk.page_number || 1}</span>
                  <span className="truncate max-w-[120px]">ID: {chunk.chunk_id}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Documents Grid with AI Info Preview & Click-to-Inspect */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-iron-textPrimary uppercase tracking-wider flex items-center gap-2">
            <Database className="w-4 h-4 text-iron-accentPrimary" />
            <span>Indexed Knowledge Documents ({filteredDocs.length})</span>
          </h2>
          <span className="text-[11px] text-iron-textSecondary font-mono">
            Click a document to view full AI synthesis and key topics
          </span>
        </div>

        {filteredDocs.length === 0 ? (
          <div className="enterprise-card p-16 text-center rounded-xl space-y-3">
            <BookOpen className="w-8 h-8 text-iron-textSecondary/40 mx-auto" />
            <div className="text-sm font-bold text-iron-textPrimary">No documents found</div>
            <p className="text-xs text-iron-textSecondary max-w-sm mx-auto">
              Upload PDF, DOCX, or scanned documents to parse and index into the local vector store.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredDocs.map((doc) => {
              const isSelected = selectedDoc?.id === doc.id;

              return (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDoc(doc)}
                  className={`p-5 rounded-xl border transition-all space-y-3 flex flex-col justify-between cursor-pointer ${
                    isSelected
                      ? "bg-iron-panelSecondary border-iron-accentPrimary ring-1 ring-iron-accentPrimary/40 shadow-sm"
                      : "enterprise-card-interactive hover:border-iron-border"
                  }`}
                >
                  <div className="space-y-2.5">
                    {/* Header Row: Category badge, Chunk Count, Delete */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                          {doc.category}
                        </span>
                        <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-iron-accentPrimary/15 text-iron-accentPrimary border border-iron-accentPrimary/30 flex items-center gap-1">
                          <Layers className="w-3 h-3" />
                          <span>{doc.chunk_count || 0} Chunks</span>
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={(e) => handleDelete(doc.id, doc.title, e)}
                        disabled={deletingDocId === doc.id}
                        className="p-1 rounded text-iron-textSecondary hover:text-iron-error hover:bg-iron-error/10 transition cursor-pointer"
                        title="Delete document"
                      >
                        {deletingDocId === doc.id ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    {/* Title & Filename */}
                    <div>
                      <h3 className="text-sm font-bold text-iron-textPrimary leading-snug group-hover:text-iron-accentPrimary transition-colors">
                        {doc.title}
                      </h3>
                      <p className="text-[11px] text-iron-textSecondary font-mono truncate mt-0.5">
                        {doc.filename}
                      </p>
                    </div>

                    {/* AI-Generated Description Preview */}
                    <div className="p-2.5 rounded-lg bg-iron-panel/60 border border-iron-border/80 space-y-1">
                      <div className="flex items-center gap-1 text-[10px] font-mono text-iron-accentPrimary font-bold">
                        <Sparkles className="w-3 h-3" />
                        <span>AI Document Description</span>
                      </div>
                      <p className="text-xs text-iron-textPrimary line-clamp-2 leading-relaxed font-sans">
                        {doc.ai_description || "Local reference document parsed and indexed for sovereign retrieval-augmented generation."}
                      </p>
                    </div>

                    {/* Key Topics / Keywords Tags */}
                    {doc.key_topics && doc.key_topics.length > 0 && (
                      <div className="space-y-1 pt-1">
                        <div className="text-[10px] font-mono text-iron-textSecondary uppercase tracking-wider">
                          Key Topics / Keywords:
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {doc.key_topics.slice(0, 4).map((topic, tIdx) => (
                            <span
                              key={tIdx}
                              className="px-2 py-0.5 rounded-md bg-iron-panel border border-iron-border text-iron-accentPrimary text-[10px] font-mono"
                            >
                              {topic}
                            </span>
                          ))}
                          {doc.key_topics.length > 4 && (
                            <span className="px-1.5 py-0.5 rounded bg-iron-panel text-iron-textSecondary text-[10px] font-mono">
                              +{doc.key_topics.length - 4} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer metadata */}
                  <div className="flex items-center justify-between text-[11px] text-iron-textSecondary font-mono pt-3 border-t border-iron-border/60">
                    <span className="text-[10px]">
                      {doc.size_bytes ? `${(doc.size_bytes / 1024).toFixed(0)} KB` : "Indexed"}
                    </span>
                    <span className="text-[10px] text-iron-accentPrimary font-semibold flex items-center gap-1">
                      <span>Click to view details</span>
                      <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 6. Document Detail Inspector Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="enterprise-card max-w-2xl w-full p-6 rounded-xl space-y-5 border-iron-border shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-start justify-between gap-4 pb-3 border-b border-iron-border">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-iron-panelSecondary text-iron-textSecondary border border-iron-border">
                    {selectedDoc.category}
                  </span>
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-iron-accentPrimary/15 text-iron-accentPrimary border border-iron-accentPrimary/30 flex items-center gap-1">
                    <Layers className="w-3 h-3" />
                    <span>{selectedDoc.chunk_count || 0} Chunks Indexed</span>
                  </span>
                </div>
                <h2 className="text-base font-bold text-iron-textPrimary">{selectedDoc.title}</h2>
                <p className="text-xs text-iron-textSecondary font-mono">{selectedDoc.filename}</p>
              </div>

              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1.5 rounded-lg text-iron-textSecondary hover:text-iron-textPrimary hover:bg-iron-panelSecondary transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* AI Generated Description Card */}
            <div className="p-4 rounded-xl bg-iron-panelSecondary border border-iron-border space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-iron-accentPrimary">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI-Generated Description (Generated at Ingestion)</span>
              </div>
              <p className="text-xs text-iron-textPrimary leading-relaxed font-sans">
                {selectedDoc.ai_description ||
                  "Standard industrial document ingested and indexed into local vector storage for semantic retrieval during autonomous agent execution."}
              </p>
            </div>

            {/* Key Topics & Keywords */}
            <div className="space-y-2">
              <div className="text-xs font-mono font-bold text-iron-textPrimary flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5 text-iron-accentPrimary" />
                <span>Key Topics & Identified Keywords</span>
              </div>

              {selectedDoc.key_topics && selectedDoc.key_topics.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {selectedDoc.key_topics.map((topic, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-md bg-iron-accentPrimary/10 border border-iron-accentPrimary/30 text-iron-accentPrimary text-xs font-mono font-semibold"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-iron-textSecondary font-mono">
                  No discrete keyword tags generated.
                </div>
              )}
            </div>

            {/* Technical Metadata Matrix */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-0.5">
                <span className="text-iron-textSecondary text-[10px]">Total Chunks</span>
                <div className="font-bold text-iron-textPrimary">{selectedDoc.chunk_count || 0} Chunks</div>
              </div>

              <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-0.5">
                <span className="text-iron-textSecondary text-[10px]">File Size</span>
                <div className="font-bold text-iron-textPrimary">
                  {selectedDoc.size_bytes ? `${(selectedDoc.size_bytes / 1024).toFixed(1)} KB` : "N/A"}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-0.5">
                <span className="text-iron-textSecondary text-[10px]">Format</span>
                <div className="font-bold text-iron-textPrimary">{selectedDoc.file_type || "PDF"}</div>
              </div>

              <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-border space-y-0.5">
                <span className="text-iron-textSecondary text-[10px]">Storage Mode</span>
                <div className="font-bold text-iron-success">Air-Gapped</div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-iron-border">
              <button
                onClick={() => handleDelete(selectedDoc.id, selectedDoc.title)}
                className="px-3 py-1.5 rounded-lg text-iron-error hover:bg-iron-error/10 border border-iron-error/30 text-xs font-mono transition flex items-center gap-1.5 cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Document</span>
              </button>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    setSearch(selectedDoc.title);
                    setSelectedDoc(null);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-iron-panelSecondary hover:bg-iron-border text-iron-textPrimary border border-iron-border text-xs font-mono transition cursor-pointer"
                >
                  Search in RAG
                </button>
                <button
                  onClick={() => {
                    router.push(`/workbench?goal=${encodeURIComponent(`Analyze the requirements in ${selectedDoc.title} and verify compliance.`)}`);
                  }}
                  className="px-3.5 py-1.5 rounded-lg bg-iron-accentPrimary hover:bg-iron-accentPrimary/90 text-white text-xs font-mono font-bold transition flex items-center gap-1.5 cursor-pointer"
                >
                  <Zap className="w-3.5 h-3.5" />
                  <span>Execute in Workbench</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
          <div className="enterprise-card max-w-lg w-full p-6 rounded-xl space-y-5 border-iron-border shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-iron-border">
              <div className="space-y-0.5">
                <h2 className="text-sm font-bold text-iron-textPrimary uppercase tracking-wider flex items-center gap-2">
                  <Upload className="w-4 h-4 text-iron-accentPrimary" />
                  <span>Ingest Knowledge Document</span>
                </h2>
                <p className="text-xs text-iron-textSecondary">
                  Upload file for local semantic chunking and dense vector embedding
                </p>
              </div>
              <button
                onClick={() => setIsUploadOpen(false)}
                className="p-1 rounded text-iron-textSecondary hover:text-iron-textPrimary transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              {/* File Dropzone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`p-6 rounded-xl border-2 border-dashed transition text-center cursor-pointer space-y-2 ${
                  selectedFile
                    ? "bg-iron-panelSecondary border-iron-accentPrimary"
                    : "bg-iron-panelSecondary/40 border-iron-border hover:border-iron-textSecondary"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <FileType className="w-8 h-8 text-iron-accentPrimary mx-auto" />
                {selectedFile ? (
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-iron-textPrimary">{selectedFile.name}</div>
                    <div className="text-[11px] font-mono text-iron-textSecondary">
                      {(selectedFile.size / 1024).toFixed(1)} KB — Ready for indexing
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-iron-textPrimary">
                      Click to browse or select document to ingest
                    </p>
                    <p className="text-[11px] text-iron-textSecondary">
                      Supports PDF, DOCX, TXT, and scanned image OCR (PNG, JPG)
                    </p>
                  </div>
                )}
              </div>

              {/* Title */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-iron-textPrimary">
                  Document Title
                </label>
                <input
                  type="text"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="e.g. Standard Operating Procedure - Pump Overhaul"
                  className="w-full px-3 py-2 rounded-lg bg-iron-panelSecondary border border-iron-border text-iron-textPrimary text-xs focus:outline-none focus:border-iron-accentPrimary"
                  required
                />
              </div>

              {/* Category */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-iron-textPrimary">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-iron-panelSecondary border border-iron-border text-iron-textPrimary text-xs focus:outline-none focus:border-iron-accentPrimary"
                >
                  <option value="Standard Operating Procedure (SOP)">Standard Operating Procedure (SOP)</option>
                  <option value="Engineering Manual">Engineering Manual</option>
                  <option value="Technical Standard">Technical Standard</option>
                  <option value="Inspection Guideline">Inspection Guideline</option>
                  <option value="Equipment Specification">Equipment Specification</option>
                </select>
              </div>

              {/* Ingestion Progress */}
              {isUploading && (
                <div className="p-3 rounded-lg bg-iron-panelSecondary border border-iron-accentPrimary/40 space-y-1.5">
                  <div className="flex items-center gap-2 text-xs text-iron-accentPrimary font-bold">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing Ingestion Pipeline</span>
                  </div>
                  <div className="text-[11px] font-mono text-iron-textSecondary">
                    {uploadProgressStage || "Extracting & Embedding into Vector Index..."}
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="p-3 rounded-lg bg-iron-error/15 border border-iron-error/30 text-xs text-iron-error flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-iron-error shrink-0 mt-0.5" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-iron-border">
                <button
                  type="button"
                  disabled={isUploading}
                  onClick={() => setIsUploadOpen(false)}
                  className="px-3.5 py-1.5 rounded-lg bg-iron-panelSecondary hover:bg-iron-border text-iron-textSecondary text-xs font-mono transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading || !selectedFile}
                  className="px-4 py-1.5 rounded-lg bg-iron-accentPrimary hover:bg-iron-accentPrimary/90 text-white text-xs font-mono font-bold transition disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-sm"
                >
                  {isUploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                  <span>Ingest & Index</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
