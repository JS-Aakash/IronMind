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
} from "lucide-react";

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [search, setSearch] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

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
      setUploadProgressStage("3/4: Generating dense vector embeddings...");

      await api.uploadKnowledgeDocument(formData);
      setUploadProgressStage("4/4: Indexed into Vector Store!");

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

  const handleDelete = async (docId: string, docTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete "${docTitle}"? All embedded chunks will be purged from the vector index.`)) {
      return;
    }
    try {
      setDeletingDocId(docId);
      await api.deleteKnowledgeDocument(docId);
      await loadDocs();
    } catch (err) {
      console.error("Failed to delete document:", err);
      alert("Failed to delete document from vector index.");
    } finally {
      setDeletingDocId(null);
    }
  };

  const handleSemanticSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!search.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      setIsSearching(true);
      const res = await api.searchKnowledge(search, 3);
      setSearchResults(res);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setIsSearching(false);
    }
  };

  const filteredDocs = documents.filter(
    (d) =>
      d.title.toLowerCase().includes(search.toLowerCase()) ||
      d.category.toLowerCase().includes(search.toLowerCase()) ||
      d.filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-3xl glass-panel relative overflow-hidden">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <BookOpen className="w-6 h-6 text-palette-periwinkle" />
            <span>Persistent Knowledge Base & Dense RAG</span>
          </h2>
          <p className="text-xs md:text-sm text-palette-ice/80">
            Self-hosted vector repository of operating procedures, technical manuals, and engineering standards.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsUploadOpen(true)}
            className="shimmer-button flex items-center gap-2 px-4 py-2 rounded-xl text-white text-xs font-semibold transition cursor-pointer shadow-lg shadow-palette-royal/30"
          >
            <Plus className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
          <button
            onClick={loadDocs}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-palette-violet/30 hover:bg-palette-violet/60 text-palette-ice text-xs font-medium transition border border-palette-periwinkle/20 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-palette-periwinkle" : ""}`} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* Upload Document Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="w-full max-w-lg rounded-3xl glass-panel p-6 space-y-5 border-palette-periwinkle/25 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-palette-periwinkle/15">
              <div className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-palette-periwinkle" />
                <h3 className="text-sm font-bold text-white">Upload to Knowledge Base</h3>
              </div>
              <button
                onClick={() => !isUploading && setIsUploadOpen(false)}
                className="p-1 rounded-lg hover:bg-palette-violet/40 text-palette-ice hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              {/* File Dropzone */}
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-palette-periwinkle/20 hover:border-palette-periwinkle rounded-2xl p-6 text-center cursor-pointer bg-palette-midnight/60 hover:bg-palette-midnight transition space-y-2"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <FileType className="w-8 h-8 text-palette-periwinkle mx-auto" />
                {selectedFile ? (
                  <div className="space-y-1">
                    <div className="text-xs font-bold text-slate-200">{selectedFile.name}</div>
                    <div className="text-[11px] font-mono text-palette-ice/70">
                      {(selectedFile.size / 1024).toFixed(1)} KB — Ready for indexing
                    </div>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-slate-200">Click or drag document here to upload</p>
                    <p className="text-[11px] text-palette-ice/60">Supports PDF, DOCX, TXT, and scanned image OCR (PNG, JPG)</p>
                  </div>
                )}
              </div>

              {/* Title */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-palette-ice">
                  Document Title
                </label>
                <input
                  type="text"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="e.g. Standard Operating Procedure - Pump Overhaul"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-palette-midnight/90 border border-palette-periwinkle/20 text-slate-100 text-xs focus:outline-none focus:border-palette-periwinkle"
                  required
                />
              </div>

              {/* Category */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-palette-ice">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-palette-midnight/90 border border-palette-periwinkle/20 text-slate-100 text-xs focus:outline-none focus:border-palette-periwinkle"
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
                <div className="p-3.5 rounded-xl bg-palette-royal/20 border border-palette-periwinkle/30 space-y-2">
                  <div className="flex items-center gap-2 text-xs text-palette-periwinkle font-bold">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-palette-periwinkle" />
                    <span>Processing Ingestion Pipeline</span>
                  </div>
                  <div className="text-[11px] font-mono text-slate-300">
                    {uploadProgressStage || "Extracting & Embedding into Vector Index..."}
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <span>{uploadError}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-palette-periwinkle/15">
                <button
                  type="button"
                  disabled={isUploading}
                  onClick={() => setIsUploadOpen(false)}
                  className="px-4 py-2 rounded-xl bg-palette-violet/30 hover:bg-palette-violet/60 text-slate-300 text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading || !selectedFile}
                  className="shimmer-button px-5 py-2 rounded-xl text-white text-xs font-bold transition disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-md shadow-palette-royal/30"
                >
                  {isUploading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                  <span>Ingest & Index</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Semantic Search Bar */}
      <form onSubmit={handleSemanticSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-palette-periwinkle/70 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Semantic search query across vector-indexed documents (e.g. 'slurry pump vibration limits')..."
            className="w-full pl-11 pr-4 py-3 rounded-2xl glass-panel text-slate-100 placeholder-palette-ice/40 text-xs focus:outline-none focus:border-palette-periwinkle transition shadow-inner"
          />
        </div>
        <button
          type="submit"
          disabled={isSearching || !search.trim()}
          className="shimmer-button px-6 py-3 rounded-2xl text-white text-xs font-semibold transition disabled:opacity-50 flex items-center gap-2 cursor-pointer shadow-lg shadow-palette-royal/30"
        >
          {isSearching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          <span>Vector Search</span>
        </button>
      </form>

      {/* Search Results Drawer */}
      {searchResults && (
        <div className="p-6 rounded-3xl glass-panel space-y-4 border-palette-royal/35">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-palette-periwinkle" />
              <h3 className="text-sm font-bold text-white">
                Dense Vector Search Results ({searchResults.chunks?.length || 0})
              </h3>
            </div>
            <button
              onClick={() => setSearchResults(null)}
              className="text-palette-ice/60 hover:text-white text-xs"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {searchResults.chunks?.map((chunk: any, i: number) => (
              <div
                key={i}
                className="p-4 rounded-2xl bg-palette-midnight/80 border border-palette-periwinkle/15 space-y-2 flex flex-col justify-between"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-mono text-palette-periwinkle">
                    <span className="font-bold truncate max-w-[180px]">
                      {chunk.document_name || "Document"}
                    </span>
                    <span>{Math.round((chunk.score || 0.8) * 100)}% Match</span>
                  </div>
                  <p className="text-xs text-palette-ice/90 leading-relaxed line-clamp-4">
                    {chunk.text}
                  </p>
                </div>
                <div className="text-[10px] text-palette-ice/50 font-mono pt-2 border-t border-palette-periwinkle/15">
                  Chunk ID: {chunk.chunk_id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Documents Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">Indexed Documents ({filteredDocs.length})</h3>
        </div>

        {filteredDocs.length === 0 ? (
          <div className="p-16 text-center rounded-3xl glass-panel space-y-3">
            <BookOpen className="w-8 h-8 text-palette-periwinkle/40 mx-auto" />
            <div className="text-sm font-semibold text-slate-300">No documents found</div>
            <p className="text-xs text-palette-ice/60 max-w-sm mx-auto">
              Upload PDF, DOCX, or scanned documents to create semantic vector indices.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredDocs.map((doc) => (
              <div
                key={doc.id}
                className="glass-panel-interactive p-5 rounded-3xl space-y-3.5 flex flex-col justify-between"
              >
                <div className="space-y-2.5">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-xl bg-palette-royal/20 flex items-center justify-center text-palette-periwinkle border border-palette-periwinkle/20">
                        <FileText className="w-4 h-4" />
                      </div>
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-palette-violet/30 text-palette-ice border border-palette-periwinkle/20">
                        {doc.category}
                      </span>
                    </div>

                    <button
                      onClick={() => handleDelete(doc.id, doc.title)}
                      disabled={deletingDocId === doc.id}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/15 transition"
                      title="Delete document & purge chunks"
                    >
                      {deletingDocId === doc.id ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  <h4 className="text-sm font-bold text-slate-100 leading-snug">{doc.title}</h4>
                  <p className="text-xs text-palette-ice/60 font-mono truncate">{doc.filename}</p>
                </div>

                <div className="flex items-center justify-between text-[11px] text-palette-ice/60 font-mono pt-3 border-t border-palette-periwinkle/15">
                  <span>{doc.chunk_count || 0} Chunks</span>
                  <span>{doc.size_bytes ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : "Indexed"}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
