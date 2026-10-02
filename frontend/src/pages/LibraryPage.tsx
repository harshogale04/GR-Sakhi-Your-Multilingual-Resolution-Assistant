import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  BookOpen,
  Search,
  Filter,
  Trash2,
  Layers,
  FileText,
  RefreshCw,
  X,
  Database,
  ChevronLeft,
  ChevronRight,
  Download,
  MessageSquareText,
  Calendar,
  Building2,
  Tag,
} from 'lucide-react';
import { api } from '../services/api';
import type { Document, Chunk } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';

const PAGE_SIZE = 15;

export const LibraryPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const selectedDocIdParam = searchParams.get('id');

  const [documents, setDocuments] = useState<Document[]>([]);
  const [totalDocs, setTotalDocs] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');

  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const fetchDocuments = useCallback(
    async (page = 1) => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getDocuments({
          page,
          limit: PAGE_SIZE,
          status: statusFilter !== 'all' ? statusFilter : undefined,
          department: departmentFilter !== 'all' ? departmentFilter : undefined,
          search: searchFilter.trim() || undefined,
        });
        setDocuments(res.items || []);
        setTotalDocs(res.total);
        setCurrentPage(res.page);
        setTotalPages(res.pages);

        if (selectedDocIdParam && res.items) {
          const found = res.items.find((d) => d.id === selectedDocIdParam);
          if (found) handleSelectDoc(found);
        }
      } catch (err) {
        console.error('Failed to load documents:', err);
        setError('Failed to load documents. Check that the backend is running.');
        setDocuments([]);
      } finally {
        setLoading(false);
      }
    },
    [searchFilter, statusFilter, departmentFilter, selectedDocIdParam],
  );

  useEffect(() => {
    fetchDocuments(1);
  }, [statusFilter, departmentFilter]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => fetchDocuments(1), 350);
    return () => clearTimeout(timer);
  }, [searchFilter]);

  const handleSelectDoc = async (doc: Document) => {
    setSelectedDoc(doc);
    setLoadingChunks(true);
    try {
      const chunkData = await api.getDocumentChunks(doc.id);
      setChunks(chunkData || []);
    } catch (err) {
      console.error('Failed to fetch chunks:', err);
      setChunks([]);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!window.confirm('Delete this resolution and its indexed vectors? This cannot be undone.')) {
      return;
    }

    setDeletingId(docId);
    setDeleteError(null);
    try {
      const result = await api.deleteDocument(docId);
      if (result.success) {
        setDocuments((prev) => prev.filter((d) => d.id !== docId));
        setTotalDocs((prev) => Math.max(0, prev - 1));
        if (selectedDoc?.id === docId) {
          setSelectedDoc(null);
          setChunks([]);
        }
      } else {
        setDeleteError(result.message || 'Deletion failed.');
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Failed to delete document. Please try again.';
      setDeleteError(detail);
    } finally {
      setDeletingId(null);
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    fetchDocuments(newPage);
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BookOpen size={18} className="text-saffron-600" />
              Government Resolution Repository (जी.आर. भांडार)
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              {totalDocs} document{totalDocs !== 1 ? 's' : ''} registered in Supabase PostgreSQL &amp; Storage
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/upload"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-navy-900 hover:bg-navy-800 rounded-lg shadow-sm transition-colors"
            >
              <FileText size={13} className="text-saffron-400" />
              Upload GR
            </Link>
            <button
              onClick={() => fetchDocuments(currentPage)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
            >
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="mt-4 flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search by Subject, GR Number, Filename..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-navy-900 font-sans"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Status Filter */}
            <div className="flex items-center gap-1.5">
              <Filter size={13} className="text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-900"
              >
                <option value="all">All Statuses / सर्व स्थिती</option>
                <option value="COMPLETED">Completed / पूर्ण</option>
                <option value="PROCESSING">Processing / प्रक्रिया सुरू</option>
                <option value="FAILED">Failed / अयशस्वी</option>
              </select>
            </div>

            {/* Department Filter */}
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-2 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-900 max-w-[180px] truncate"
            >
              <option value="all">All Departments / सर्व विभाग</option>
              <option value="School Education">School Education</option>
              <option value="Finance">Finance</option>
              <option value="Agriculture">Agriculture</option>
              <option value="Public Health">Public Health</option>
              <option value="Revenue & Forest">Revenue & Forest</option>
              <option value="Urban Development">Urban Development</option>
            </select>
          </div>
        </div>
      </div>

      {/* Delete Error Banner */}
      {deleteError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
          <span>{deleteError}</span>
          <button onClick={() => setDeleteError(null)} className="ml-3 text-rose-600 hover:text-rose-800">
            <X size={13} />
          </button>
        </div>
      )}

      {/* Main Table + Inspector Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div
          className={`${selectedDoc ? 'lg:col-span-2' : 'lg:col-span-3'} bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden transition-all`}
        >
          {loading ? (
            <LoadingSpinner label="Loading document records from Supabase..." />
          ) : error ? (
            <div className="p-8 text-center text-xs text-rose-600">
              <p className="font-semibold">Connection Error</p>
              <p className="mt-1 text-rose-500">{error}</p>
              <button
                onClick={() => fetchDocuments(1)}
                className="mt-3 px-4 py-1.5 bg-rose-100 hover:bg-rose-200 rounded-lg font-medium text-rose-700"
              >
                Retry
              </button>
            </div>
          ) : documents.length === 0 ? (
            <EmptyState
              icon={FileText}
              title="No Matching Government Resolutions"
              marathiTitle="कोणतेही शासन निर्णय सापडले नाहीत"
              description={
                totalDocs === 0
                  ? 'The document repository is empty. Upload your first Maharashtra GR to start building the vector search index.'
                  : 'No records matched your search query or filters.'
              }
              actionLabel={totalDocs === 0 ? 'Upload Resolution' : 'Clear Filters'}
              onAction={
                totalDocs === 0
                  ? () => (window.location.href = '/upload')
                  : () => {
                      setSearchFilter('');
                      setStatusFilter('all');
                      setDepartmentFilter('all');
                    }
              }
            />
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/80 text-slate-500 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Resolution Details</th>
                      <th className="px-4 py-3">Department / Category</th>
                      <th className="px-4 py-3">Pages / Chunks</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Uploaded</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {documents.map((doc) => {
                      const isSelected = selectedDoc?.id === doc.id;
                      return (
                        <tr
                          key={doc.id}
                          onClick={() => handleSelectDoc(doc)}
                          className={`cursor-pointer transition-colors ${
                            isSelected ? 'bg-navy-50/60' : 'hover:bg-slate-50/70'
                          }`}
                        >
                          <td className="px-4 py-3 max-w-xs">
                            <div
                              className="font-semibold text-slate-900 line-clamp-1 font-sans"
                              title={doc.subject || doc.original_filename}
                            >
                              {doc.subject || doc.original_filename}
                            </div>
                            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono mt-0.5">
                              {doc.gr_number ? (
                                <span className="text-slate-700 bg-slate-100 px-1 py-0.5 rounded font-mono">
                                  {doc.gr_number}
                                </span>
                              ) : (
                                <span className="truncate max-w-[150px]">{doc.filename}</span>
                              )}
                              <span className="text-slate-400 uppercase font-sans font-medium text-[10px]">
                                • {doc.language || 'MR'}
                              </span>
                            </div>
                          </td>

                          <td className="px-4 py-3 text-slate-600">
                            <div className="font-medium text-slate-800">{doc.department || 'General'}</div>
                            {doc.category && (
                              <div className="text-[10px] text-slate-400">{doc.category}</div>
                            )}
                          </td>

                          <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                            {doc.pages ?? '-'} pgs / {doc.chunk_count ?? '-'} chunks
                          </td>

                          <td className="px-4 py-3">
                            <StatusBadge status={doc.status} size="sm" />
                          </td>

                          <td className="px-4 py-3 text-slate-500 text-[11px]">
                            {new Date(doc.uploaded_at).toLocaleDateString()}
                          </td>

                          <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => handleSelectDoc(doc)}
                                className="text-xs text-navy-800 font-semibold hover:underline"
                              >
                                Inspect
                              </button>
                              <a
                                href={api.getDocumentDownloadUrl(doc.id)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-slate-500 hover:text-emerald-700 p-1 rounded hover:bg-emerald-50 transition-colors"
                                title="Download / Preview Original PDF"
                              >
                                <Download size={13} />
                              </a>
                              <button
                                type="button"
                                disabled={deletingId === doc.id}
                                onClick={() => handleDelete(doc.id)}
                                className="text-slate-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 transition-colors disabled:opacity-40"
                                title="Delete Resolution"
                              >
                                <Trash2 size={13} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <span>
                    Page {currentPage} of {totalPages} · {totalDocs} total
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage <= 1}
                      className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft size={14} />
                    </button>
                    <button
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage >= totalPages}
                      className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <ChevronRight size={14} />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Selected Document Details & Chunks Drawer */}
        {selectedDoc && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-5 flex flex-col justify-between max-h-[850px] overflow-y-auto">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Database size={15} className="text-saffron-600" />
                  <h3 className="text-xs font-bold text-slate-900">Document Details</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedDoc(null)}
                  className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                >
                  <X size={15} />
                </button>
              </div>

              {/* Document Metadata Details */}
              <div className="mt-4 space-y-3 text-xs">
                <div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Subject (विषय)</span>
                  <p className="font-semibold text-slate-900 mt-0.5 leading-snug font-sans">
                    {selectedDoc.subject || 'N/A'}
                  </p>
                </div>

                <div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Original Filename</span>
                  <p className="text-slate-600 font-mono text-[11px] truncate">{selectedDoc.original_filename}</p>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                      <Building2 size={11} /> Department
                    </span>
                    <p className="text-slate-800 font-medium mt-0.5">{selectedDoc.department || 'General'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">GR Number</span>
                    <p className="text-slate-800 font-mono text-[11px] mt-0.5">{selectedDoc.gr_number || 'N/A'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                      <Tag size={11} /> Category
                    </span>
                    <p className="text-slate-800 font-medium mt-0.5">{selectedDoc.category || 'Policy'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Doc Type</span>
                    <p className="text-slate-800 font-medium mt-0.5">{selectedDoc.document_type || 'GR'}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Language</span>
                    <p className="text-slate-800 uppercase font-medium mt-0.5">{selectedDoc.language || 'mr'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Status</span>
                    <div className="mt-0.5">
                      <StatusBadge status={selectedDoc.status} size="sm" />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                      <Calendar size={11} /> Uploaded Date
                    </span>
                    <p className="text-slate-700 mt-0.5">{new Date(selectedDoc.uploaded_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Pages / Chunks</span>
                    <p className="text-slate-800 font-mono mt-0.5">{selectedDoc.pages ?? '—'} pgs · {selectedDoc.chunk_count ?? '—'} chunks</p>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Storage Path</span>
                  <p className="text-[11px] font-mono text-slate-500 bg-slate-50 p-1.5 rounded border border-slate-200/70 truncate mt-0.5">
                    {selectedDoc.storage_path}
                  </p>
                </div>
              </div>

              {/* Action Buttons for Document */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col gap-2">
                <a
                  href={api.getDocumentDownloadUrl(selectedDoc.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
                >
                  <Download size={13} />
                  Download / Preview Original PDF
                </a>

                <div className="grid grid-cols-2 gap-2">
                  <Link
                    to={`/ask`}
                    className="inline-flex items-center justify-center gap-1 py-1.5 px-2 bg-navy-900 hover:bg-navy-800 text-white rounded-lg text-xs font-medium transition-colors"
                  >
                    <MessageSquareText size={12} />
                    Ask AI
                  </Link>
                  <Link
                    to={`/search?q=${encodeURIComponent(selectedDoc.subject || selectedDoc.original_filename)}`}
                    className="inline-flex items-center justify-center gap-1 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-medium transition-colors"
                  >
                    <Search size={12} />
                    Search Related
                  </Link>
                </div>
              </div>

              {/* Relational Chunks Registry (PostgreSQL chunks table) */}
              <div className="mt-5 pt-3 border-t border-slate-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                    <Layers size={13} className="text-navy-800" />
                    Chunks Registry ({chunks.length})
                  </span>
                  <span className="text-[10px] text-slate-400">PostgreSQL 'chunks' table</span>
                </div>

                {loadingChunks ? (
                  <div className="py-4 text-center">
                    <LoadingSpinner label="Fetching registered chunks..." size={16} />
                  </div>
                ) : chunks.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">
                    {selectedDoc.status === 'PROCESSING'
                      ? 'Processing in progress — chunks will appear once vectorization completes.'
                      : 'No registered chunks found for this document.'}
                  </p>
                ) : (
                  <div className="space-y-1.5 max-h-52 overflow-y-auto pr-1">
                    {chunks.map((chk, idx) => (
                      <div
                        key={chk.id}
                        className="p-2 rounded bg-slate-50 border border-slate-200/80 text-[11px] flex items-center justify-between"
                      >
                        <div>
                          <span className="font-semibold text-slate-800">Chunk #{idx + 1}</span>
                          <span className="text-slate-500 ml-1.5">Page {chk.page ?? '-'}</span>
                          {chk.section && <span className="text-slate-500 ml-1">({chk.section})</span>}
                        </div>
                        <span
                          className="font-mono text-[10px] text-slate-400 truncate max-w-[110px]"
                          title={chk.pinecone_id}
                        >
                          {chk.pinecone_id}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                <p className="text-[10px] text-slate-400 mt-2 leading-tight">
                  * Note: Raw chunk text and vector embeddings are stored in Pinecone metadata. The PostgreSQL table maintains relational integrity.
                </p>
              </div>
            </div>

            {/* Delete button at bottom */}
            <div className="mt-5 pt-3 border-t border-slate-100">
              <button
                type="button"
                disabled={deletingId === selectedDoc.id}
                onClick={() => handleDelete(selectedDoc.id)}
                className="w-full py-2 px-3 border border-rose-200 hover:bg-rose-50 text-rose-600 rounded-lg text-xs font-semibold transition-colors disabled:opacity-40 flex items-center justify-center gap-1.5"
              >
                <Trash2 size={13} />
                <span>Delete Government Resolution</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
