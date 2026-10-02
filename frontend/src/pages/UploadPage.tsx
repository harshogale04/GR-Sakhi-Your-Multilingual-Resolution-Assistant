import React, { useState, useEffect, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import type { DocumentUploadResponse, DocumentStatusResponse, DocumentStatus } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';

export const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [department, setDepartment] = useState('School Education');
  const [grNumber, setGrNumber] = useState('');
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState('Policy');
  const [language, setLanguage] = useState('mr');
  const [documentType, setDocumentType] = useState('Government Resolution');

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedDoc, setUploadedDoc] = useState<DocumentUploadResponse | null>(null);
  const [docStatus, setDocStatus] = useState<DocumentStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll status after upload until COMPLETED or FAILED
  useEffect(() => {
    if (!uploadedDoc) return;

    const poll = async () => {
      try {
        const s = await api.getDocumentStatus(uploadedDoc.id);
        setDocStatus(s);
        if (s.status === 'COMPLETED' || s.status === 'FAILED') {
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch {
        // Status polling failure is non-fatal — the doc was uploaded
      }
    };

    // Poll immediately, then every 4 seconds
    poll();
    pollingRef.current = setInterval(poll, 4000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [uploadedDoc]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      if (selected.type !== 'application/pdf') {
        setError('Only PDF documents (.pdf) are supported for Maharashtra Government Resolutions.');
        setFile(null);
        return;
      }
      setFile(selected);
      setError(null);
      if (!subject) {
        setSubject(selected.name.replace(/\.pdf$/i, '').replace(/[-_]/g, ' '));
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      if (selected.type !== 'application/pdf') {
        setError('Only PDF documents (.pdf) are supported.');
        return;
      }
      setFile(selected);
      setError(null);
      if (!subject) {
        setSubject(selected.name.replace(/\.pdf$/i, '').replace(/[-_]/g, ' '));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a Government Resolution PDF file.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadedDoc(null);
    setDocStatus(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('department', department);
      formData.append('gr_number', grNumber);
      formData.append('subject', subject);
      formData.append('category', category);
      formData.append('language', language);
      formData.append('document_type', documentType);

      const response = await api.uploadDocument(formData, (percent) => {
        setUploadProgress(percent);
      });

      setUploadedDoc(response);
      // Reset form fields
      setFile(null);
      setGrNumber('');
      setSubject('');
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(
        err?.response?.data?.detail ||
          'Failed to upload document. Please check the backend connection.',
      );
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const effectiveStatus: DocumentStatus = (docStatus?.status ?? uploadedDoc?.status ?? 'PROCESSING') as DocumentStatus;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-6">
        <div className="max-w-2xl">
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <UploadCloud size={20} className="text-saffron-600" />
            Upload Government Resolution (जी.आर. अपलोड)
          </h1>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Upload Marathi, Hindi, or English Government Resolution PDFs. The pipeline stores the
            original document in Supabase Storage, extracts text via PyPDF/OCR, creates vector
            embeddings via Gemini{' '}
            <code className="bg-slate-100 text-slate-700 px-1 py-0.5 rounded font-mono">
              gemini-embedding-001
            </code>
            , and indexes chunks into Pinecone. Processing runs in the background — you can track
            status below.
          </p>
        </div>
      </div>

      {/* Upload Success + Live Status */}
      {uploadedDoc && (
        <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 shadow-subtle">
          <div className="flex items-start gap-3">
            <CheckCircle2 size={20} className="text-emerald-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-xs font-bold text-emerald-900">
                Resolution Uploaded — Background Processing Active
              </h3>
              <p className="text-xs text-emerald-700 mt-1">
                <span className="font-semibold">{uploadedDoc.original_filename}</span> is registered.
                Text extraction, embedding, and vector indexing are running in the background.
              </p>

              {/* Live status row */}
              <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px]">
                <span className="font-mono bg-emerald-100/70 px-2 py-0.5 rounded text-emerald-800">
                  ID: {uploadedDoc.id}
                </span>
                <div className="flex items-center gap-1.5">
                  <span className="text-emerald-700 font-medium">Status:</span>
                  <StatusBadge status={effectiveStatus} size="sm" />
                  {effectiveStatus === 'PROCESSING' && (
                    <RefreshCw size={11} className="animate-spin text-emerald-600 ml-1" />
                  )}
                </div>
                {docStatus?.pages && (
                  <span className="text-emerald-700">
                    {docStatus.pages} pages · {docStatus.chunk_count ?? '?'} chunks
                  </span>
                )}
              </div>

              {effectiveStatus === 'COMPLETED' && (
                <p className="mt-2 text-[11px] text-emerald-700 font-medium">
                  ✓ Indexing complete — document is now searchable in the RAG system.
                </p>
              )}
              {effectiveStatus === 'FAILED' && (
                <p className="mt-2 text-[11px] text-rose-600 font-medium">
                  ✗ Processing failed. The file was stored but indexing encountered an error.
                </p>
              )}
            </div>

            <a
              href="/ask"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors flex-shrink-0"
            >
              <Sparkles size={13} />
              <span>Ask AI</span>
            </a>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-900 flex items-start gap-3">
          <AlertCircle size={18} className="text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs">
            <p className="font-semibold">Upload failed</p>
            <p className="mt-0.5 text-rose-700">{error}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-subtle p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Drag & Drop File Zone */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                Resolution PDF Document <span className="text-rose-500">*</span>
              </label>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                  file
                    ? 'border-emerald-300 bg-emerald-50/30'
                    : 'border-slate-300 hover:border-navy-500 bg-slate-50/50'
                }`}
              >
                <input
                  type="file"
                  id="gr-file-input"
                  accept="application/pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label htmlFor="gr-file-input" className="cursor-pointer">
                  <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-500 mb-2">
                    {file ? (
                      <FileText size={22} className="text-emerald-600" />
                    ) : (
                      <UploadCloud size={22} className="text-navy-800" />
                    )}
                  </div>
                  {file ? (
                    <div>
                      <p className="text-xs font-bold text-slate-900">{file.name}</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB · Ready to process
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-xs font-semibold text-slate-800">
                        Click to upload or drag &amp; drop Maharashtra GR PDF
                      </p>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Supports Marathi / Hindi / English government circulars (Max 50 MB)
                      </p>
                    </div>
                  )}
                </label>
              </div>
            </div>

            {/* Subject / Title */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Subject / Title (विषय) <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="उदा. छत्रपती शिवाजी महाराज शेतकरी सन्मान योजना नियमावली"
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-1 focus:ring-navy-900"
              />
            </div>

            {/* GR Number & Department */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  GR Number (शासन निर्णय क्रमांक)
                </label>
                <input
                  type="text"
                  value={grNumber}
                  onChange={(e) => setGrNumber(e.target.value)}
                  placeholder="उदा. संकीर्ण-२०२४/प्र.क्र.४५/का.१२"
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-navy-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Department (विभाग)
                </label>
                <select
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-navy-900"
                >
                  <option value="School Education">School Education / शालेय शिक्षण</option>
                  <option value="Finance">Finance / वित्त विभाग</option>
                  <option value="Agriculture">Agriculture / कृषी व शेतकरी कल्याण</option>
                  <option value="Public Health">Public Health / सार्वजनिक आरोग्य</option>
                  <option value="Revenue & Forest">Revenue &amp; Forest / महसूल व वन</option>
                  <option value="Urban Development">Urban Development / नगर विकास</option>
                  <option value="Rural Development">Rural Development / ग्राम विकास</option>
                  <option value="Higher Education">Higher &amp; Technical Education / उच्च शिक्षण</option>
                  <option value="General Administration">General Administration / सामान्य प्रशासन</option>
                </select>
              </div>
            </div>

            {/* Category & Language */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category (वर्गवारी)
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-navy-900"
                >
                  <option value="Policy">Policy / धोरण</option>
                  <option value="Scheme">Scheme / योजना व अनुदान</option>
                  <option value="Recruitment">Recruitment / पदभरती</option>
                  <option value="Financial">Financial / आर्थिक तरतूद</option>
                  <option value="Transfer">Transfer / बदल्या व पदोन्नती</option>
                  <option value="Circular">Circular / परिपत्रक</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Document Language (भाषा)
                </label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-navy-900"
                >
                  <option value="mr">Marathi (मराठी) — Primary</option>
                  <option value="hi">Hindi (हिंदी)</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>

            {/* Document Type */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Document Type (दस्तावेज प्रकार)
              </label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-navy-900"
              >
                <option value="Government Resolution">Government Resolution / शासन निर्णय (GR)</option>
                <option value="Circular">Circular / परिपत्रक</option>
                <option value="Official Gazette">Official Gazette / राजपत्र</option>
                <option value="Order">Order / आदेश</option>
              </select>
            </div>

            {/* Upload Progress Bar */}
            {uploading && uploadProgress > 0 && (
              <div>
                <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                  <span>Uploading to Supabase Storage…</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5">
                  <div
                    className="bg-navy-900 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={uploading || !file}
                className="w-full py-2.5 px-4 bg-navy-900 hover:bg-navy-800 disabled:opacity-40 text-white rounded-xl text-xs font-bold shadow-sm transition-all flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Clock size={14} className="animate-spin text-saffron-400" />
                    <span>Uploading ({uploadProgress}%)…</span>
                  </>
                ) : (
                  <>
                    <UploadCloud size={15} className="text-saffron-400" />
                    <span>Upload &amp; Index Resolution</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Processing Pipeline Flow Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-5 flex flex-col justify-between">
          <div>
            <div className="pb-3 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                <Layers size={14} className="text-saffron-600" />
                Dual-Store Ingestion Flow
              </h3>
              <span className="text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-bold">
                Background
              </span>
            </div>

            <ol className="mt-4 relative border-l border-slate-200 ml-2 space-y-4 text-xs">
              <li className="ml-4">
                <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-navy-900 border border-white" />
                <h4 className="font-semibold text-slate-800">1. Supabase Storage Bucket</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Stores original unmodified PDF securely. Returns immediately with PROCESSING status.
                </p>
              </li>

              <li className="ml-4">
                <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-navy-900 border border-white" />
                <h4 className="font-semibold text-slate-800">2. Text Extraction &amp; OCR</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  PyPDF text extraction with Tesseract OCR fallback for scanned Devanagari pages.
                </p>
              </li>

              <li className="ml-4">
                <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-navy-900 border border-white" />
                <h4 className="font-semibold text-slate-800">3. Gemini Vector Embeddings</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Each chunk embedded using{' '}
                  <code className="font-mono text-slate-700">gemini-embedding-001</code>.
                </p>
              </li>

              <li className="ml-4">
                <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-saffron-500 border border-white" />
                <h4 className="font-semibold text-slate-800">4. Pinecone Upsert</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Embeddings + chunk text &amp; metadata stored in Pinecone vector index.
                </p>
              </li>

              <li className="ml-4">
                <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-emerald-600 border border-white" />
                <h4 className="font-semibold text-slate-800">5. Relational Chunk Registry</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Mappings registered into PostgreSQL{' '}
                  <code className="font-mono text-slate-700">chunks</code> table. Status set to{' '}
                  <strong>COMPLETED</strong>.
                </p>
              </li>
            </ol>
          </div>

          <div className="mt-5 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
            Compliant with existing Supabase schema constraints. No extra tables created.
          </div>
        </div>
      </div>
    </div>
  );
};
