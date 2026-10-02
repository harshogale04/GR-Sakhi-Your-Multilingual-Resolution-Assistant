import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Layers,
  MessageSquareText,
  Search,
  UploadCloud,
  ArrowRight,
  Database,
  Cpu,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
  CheckCircle2,
  Clock,
  AlertOctagon,
} from 'lucide-react';
import { StatCard } from '../components/common/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';
import { api } from '../services/api';
import type { Document, DocumentStats } from '../types';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, docsData] = await Promise.allSettled([
        api.getStats(),
        api.getDocuments({ limit: 6 }),
      ]);

      if (statsData.status === 'fulfilled') {
        setStats(statsData.value);
      } else {
        setStats({
          total_documents: 0,
          total_chunks: 0,
          completed_documents: 0,
          indexed_documents: 0,
          processing_documents: 0,
          failed_documents: 0,
          departments_count: 0,
          language_breakdown: { mr: 0, hi: 0, en: 0 },
        });
      }

      if (docsData.status === 'fulfilled') {
        setRecentDocs(docsData.value.items ?? []);
      } else {
        setRecentDocs([]);
      }
    } catch {
      setError('Unable to reach backend services. Please ensure the FastAPI server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-navy-950 via-navy-900 to-navy-800 text-white p-6 md:p-8 shadow-elevated border border-navy-800">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-saffron-500/20 text-saffron-300 border border-saffron-500/30 text-xs font-semibold mb-3">
            <span>🇮🇳 AI for Bharat Hackathon Solution</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            MAHA-GR: Multilingual AI for Maharashtra Government Resolutions
          </h1>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed font-normal">
            महाराष्ट्र शासन निर्णयांची माहिती आता सर्वांसाठी सुलभ, पारदर्शक आणि गतिमान.
            Ask questions, search official government resolutions, and receive fact-checked answers with verified document and page citations in Marathi, Hindi, and English.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Link
              to="/ask"
              className="inline-flex items-center gap-2 px-4 py-2 bg-saffron-500 hover:bg-saffron-600 text-white text-xs font-semibold rounded-lg shadow-sm transition-all"
            >
              <MessageSquareText size={15} />
              <span>Ask AI in Marathi / प्रश्न विचारा</span>
            </Link>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-xs font-medium rounded-lg backdrop-blur-sm border border-white/15 transition-all"
            >
              <UploadCloud size={15} />
              <span>Upload GR PDF</span>
            </Link>
          </div>
        </div>

        {/* Subtle Decorative Backdrop Element */}
        <div className="absolute right-0 top-0 bottom-0 w-80 bg-gradient-to-l from-saffron-500/10 via-transparent to-transparent pointer-events-none" />
      </div>

      {/* Connectivity Error Banner if any */}
      {error && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200/90 text-amber-900 flex items-start gap-3">
          <ShieldAlert size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-xs">
            <p className="font-semibold">{error}</p>
            <p className="mt-0.5 text-amber-700">
              Check backend running on port 8000. Start backend with <code className="bg-amber-100 px-1 py-0.5 rounded font-mono">uvicorn app.main:app --reload</code>.
            </p>
          </div>
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-md bg-amber-200/80 text-amber-800 hover:bg-amber-200"
          >
            <RefreshCw size={12} />
            Retry
          </button>
        </div>
      )}

      {/* Required Live Statistics Grid */}
      <div>
        <div className="flex items-center justify-between mb-3 px-1">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Repository Live Metrics (वास्तविक आकडेवारी)
          </h2>
          <button
            onClick={fetchData}
            className="text-[11px] text-slate-500 hover:text-navy-900 flex items-center gap-1 font-medium"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh Stats
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3.5">
          {/* Total Documents */}
          <StatCard
            title="Total Documents"
            marathiTitle="एकूण शासन निर्णय"
            value={stats?.total_documents ?? 0}
            icon={FileText}
            description="Registered in Supabase DB"
            accentColor="navy"
          />

          {/* Completed Documents */}
          <StatCard
            title="Completed"
            marathiTitle="पूर्ण झालेले"
            value={stats?.completed_documents ?? stats?.indexed_documents ?? 0}
            icon={CheckCircle2}
            description="Fully processed & searchable"
            accentColor="green"
          />

          {/* Processing Documents */}
          <StatCard
            title="Processing"
            marathiTitle="प्रक्रिया सुरू"
            value={stats?.processing_documents ?? 0}
            icon={Clock}
            description="OCR & vectorization active"
            accentColor="amber"
          />

          {/* Failed Documents */}
          <StatCard
            title="Failed"
            marathiTitle="अयशस्वी"
            value={stats?.failed_documents ?? 0}
            icon={AlertOctagon}
            description="Extraction/indexing issues"
            accentColor="rose"
          />

          {/* Total Indexed Chunks */}
          <StatCard
            title="Indexed Chunks"
            marathiTitle="पिनेकॉन व्हेक्टर तुकडे"
            value={stats?.total_chunks ?? 0}
            icon={Layers}
            description="Stored in Pinecone vector index"
            accentColor="saffron"
          />
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/ask"
          className="group p-5 bg-white rounded-xl border border-slate-200 shadow-subtle hover:border-navy-300 hover:shadow-card transition-all"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-navy-50 text-navy-800 group-hover:bg-navy-900 group-hover:text-white transition-colors">
              <MessageSquareText size={20} />
            </div>
            <ArrowRight size={16} className="text-slate-400 group-hover:translate-x-1 group-hover:text-navy-900 transition-all" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Ask AI in Indian Languages</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Query Maharashtra GRs naturally. Get grounded answers with direct document citations and page references.
          </p>
        </Link>

        <Link
          to="/search"
          className="group p-5 bg-white rounded-xl border border-slate-200 shadow-subtle hover:border-navy-300 hover:shadow-card transition-all"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-saffron-50 text-saffron-600 group-hover:bg-saffron-500 group-hover:text-white transition-colors">
              <Search size={20} />
            </div>
            <ArrowRight size={16} className="text-slate-400 group-hover:translate-x-1 group-hover:text-saffron-600 transition-all" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Multilingual Semantic Search</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Search cross-lingual concepts using Gemini embeddings. Filter by department, category, and date.
          </p>
        </Link>

        <Link
          to="/upload"
          className="group p-5 bg-white rounded-xl border border-slate-200 shadow-subtle hover:border-navy-300 hover:shadow-card transition-all"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
              <UploadCloud size={20} />
            </div>
            <ArrowRight size={16} className="text-slate-400 group-hover:translate-x-1 group-hover:text-emerald-600 transition-all" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">Upload &amp; Process GRs</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Directly upload PDF resolutions. Automatic OCR fallback, chunking, and dual-storage indexing.
          </p>
        </Link>
      </div>

      {/* Main Two-Column Section: Recent Documents & RAG Architecture Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent GRs Table */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/90 shadow-subtle overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Recent Government Resolutions</h3>
              <p className="text-xs text-slate-500">नुकतेच अपलोड केलेले शासन निर्णय</p>
            </div>
            <Link
              to="/library"
              className="text-xs font-semibold text-navy-800 hover:text-navy-900 hover:underline flex items-center gap-1"
            >
              View all library <ArrowRight size={12} />
            </Link>
          </div>

          {loading ? (
            <LoadingSpinner label="Loading recent documents..." />
          ) : recentDocs.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No Government Resolutions Indexed Yet"
              marathiTitle="अद्याप कोणतेही शासन निर्णय उपलब्ध नाहीत"
              description="Upload your first Maharashtra Government Resolution PDF to begin semantic search and multilingual AI Q&A."
              actionLabel="Upload First GR"
              onAction={() => window.location.href = '/upload'}
            />
          ) : (
            <div className="divide-y divide-slate-100 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50/70 text-slate-500 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3">GR Document</th>
                    <th className="px-4 py-3">Department</th>
                    <th className="px-4 py-3">Language</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 line-clamp-1 max-w-xs" title={doc.subject || doc.original_filename}>
                          {doc.subject || doc.original_filename}
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {doc.gr_number || doc.filename}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {doc.department || 'General'}
                      </td>
                      <td className="px-4 py-3 text-slate-500 font-medium">
                        {doc.language ? doc.language.toUpperCase() : 'MR'}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={doc.status} size="sm" />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          to={`/library?id=${doc.id}`}
                          className="text-xs font-semibold text-navy-800 hover:text-navy-900 inline-flex items-center gap-1"
                        >
                          Details <ExternalLink size={11} />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* System Architecture & Status Card */}
        <div className="bg-white rounded-xl border border-slate-200/90 shadow-subtle p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Cpu size={16} className="text-saffron-600" />
                Pipeline Architecture
              </h3>
              <span className="text-[10px] uppercase font-semibold text-slate-400">Stack</span>
            </div>

            <div className="mt-4 space-y-3.5 text-xs">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-3">
                <Database size={16} className="text-navy-800 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-semibold text-slate-800">Supabase Relational Core</div>
                  <div className="text-[11px] text-slate-500">
                    Tables: <code className="font-mono text-slate-700 font-medium">documents</code> &amp; <code className="font-mono text-slate-700 font-medium">chunks</code> registry (unchanged schema).
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-3">
                <Layers size={16} className="text-saffron-600 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-semibold text-slate-800">Pinecone Vector Database</div>
                  <div className="text-[11px] text-slate-500">
                    High-dimension embeddings storing chunk content &amp; metadata for fast retrieval.
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-3">
                <Cpu size={16} className="text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-semibold text-slate-800">Google Gemini Flash + Embeddings</div>
                  <div className="text-[11px] text-slate-500">
                    <code className="font-mono text-slate-700">gemini-embedding-001</code> &amp; Gemini Flash multilingual generation.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span>Grounding: Strict Evidence Retrieval</span>
            <span className="text-emerald-600 font-medium">OCR Fallback Active</span>
          </div>
        </div>
      </div>
    </div>
  );
};
