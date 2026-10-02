import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Search as SearchIcon,
  Filter,
  Bookmark,
  Sparkles,
  ExternalLink,
  MessageSquareText,
  SlidersHorizontal,
  FileText,
  Languages,
} from 'lucide-react';
import { api } from '../services/api';
import type { SearchResult, Language } from '../types';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { EmptyState } from '../components/common/EmptyState';

interface SearchPageProps {
  currentLanguage: Language;
}

export const SearchPage: React.FC<SearchPageProps> = ({ currentLanguage }) => {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const initialDept = searchParams.get('dept') || 'all';

  const [query, setQuery] = useState(initialQuery);
  const [searchLang, setSearchLang] = useState<Language>(currentLanguage);
  const [department, setDepartment] = useState(initialDept);
  const [topK, setTopK] = useState(10);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [totalResults, setTotalResults] = useState(0);

  const departments = [
    { value: 'all', label: 'All Departments / सर्व विभाग' },
    { value: 'School Education', label: 'School Education / शालेय शिक्षण विभाग' },
    { value: 'Finance', label: 'Finance Department / वित्त विभाग' },
    { value: 'Agriculture', label: 'Agriculture / कृषी व शेतकरी कल्याण' },
    { value: 'Public Health', label: 'Public Health / सार्वजनिक आरोग्य विभाग' },
    { value: 'Revenue & Forest', label: 'Revenue & Forest / महसूल व वन विभाग' },
    { value: 'Urban Development', label: 'Urban Development / नगर विकास विभाग' },
    { value: 'Rural Development', label: 'Rural Development / ग्राम विकास विभाग' },
    { value: 'General Administration', label: 'General Administration / सामान्य प्रशासन' },
  ];

  const executeSearch = async (searchQueryText: string) => {
    if (!searchQueryText.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const response = await api.searchGR({
        query: searchQueryText.trim(),
        language: searchLang,
        department: department === 'all' ? undefined : department,
        top_k: topK,
      });

      setResults(response.results || []);
      setTotalResults(response.total || response.results?.length || 0);
    } catch (err: any) {
      console.error('Search error:', err);
      setResults([]);
      setTotalResults(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      executeSearch(initialQuery);
    }
  }, [initialQuery]);

  const handleSearch = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    executeSearch(query);
  };

  const sampleSearches = [
    'शेतकरी कर्जमाफी शासन निर्णय',
    'शिक्षक भरती व पात्रता निकष',
    'शासकीय कर्मचाऱ्यांची रजा नियमावली',
    'ठिबक सिंचन योजना अनुदान',
    'सार्वजनिक आरोग्य वैद्यकीय अधिकारी भरती',
  ];

  const getRelevanceBadge = (score?: number) => {
    if (!score || score >= 0.70) {
      return (
        <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-semibold">
          High Relevance / उच्च प्रासंगिकता
        </span>
      );
    }
    if (score >= 0.45) {
      return (
        <span className="px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-800 border border-sky-200 text-[11px] font-semibold">
          Direct Match / संबंधित संदर्भ
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-semibold">
        Related Passage / संबंधित परिच्छेद
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header and Search Controls */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-6">
        <div className="max-w-3xl">
          <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <SearchIcon size={20} className="text-saffron-600" />
            Multilingual Semantic Search for Maharashtra GRs
          </h1>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed font-sans">
            पिनेकॉन व्हेक्टर डेटाबेस आणि <code className="bg-slate-100 text-slate-700 px-1 py-0.5 rounded font-mono">gemini-embedding-001</code> आधारित अर्थपूर्ण शोध.
            Search concepts across Marathi, Hindi, and English even when exact administrative words differ.
          </p>
        </div>

        {/* Search Bar Form */}
        <form onSubmit={handleSearch} className="mt-5 space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <SearchIcon size={16} className="absolute left-3.5 top-3.5 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="उदा. दुष्काळ निवारण निधी, अनुदान, शिक्षक भरती, पदोन्नती नियम, शेतकरी योजना..."
                className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-navy-900/15 focus:border-navy-900 transition-all font-sans"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-2.5 bg-navy-900 hover:bg-navy-800 disabled:opacity-40 text-white rounded-xl text-xs font-semibold shadow-sm transition-all flex items-center justify-center gap-2 flex-shrink-0"
            >
              <SearchIcon size={14} className="text-saffron-400" />
              <span>Search GRs</span>
            </button>
          </div>

          {/* Filters Row */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {/* Language Selector */}
            <div className="flex items-center gap-1.5">
              <Languages size={13} className="text-slate-400" />
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Language:</span>
              <select
                value={searchLang}
                onChange={(e) => setSearchLang(e.target.value as Language)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-800"
              >
                <option value="mr">मराठी (Marathi)</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="en">English</option>
              </select>
            </div>

            {/* Department Filter */}
            <div className="flex items-center gap-1.5">
              <Filter size={13} className="text-slate-400" />
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Department:</span>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-800 max-w-[220px] truncate"
              >
                {departments.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Top K */}
            <div className="flex items-center gap-1.5">
              <SlidersHorizontal size={13} className="text-slate-400" />
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Results:</span>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-800"
              >
                <option value={5}>Top 5</option>
                <option value={10}>Top 10</option>
                <option value={20}>Top 20</option>
              </select>
            </div>
          </div>

          {/* Quick search tags */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-400">
            <span>Popular searches:</span>
            {sampleSearches.map((tag, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(tag);
                  executeSearch(tag);
                }}
                className="px-2 py-0.5 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors font-sans"
              >
                {tag}
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Results Section */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-subtle">
            <LoadingSpinner label="Searching vector embeddings in Pinecone..." />
          </div>
        ) : searched && results.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-subtle">
            <EmptyState
              icon={SearchIcon}
              title="No Matching Resolution Passages Found"
              marathiTitle="कोणतेही संबंधित उतारे आढळले नाहीत"
              description="Try broadening your search query or removing department filters. Ensure relevant Maharashtra GRs have been uploaded and indexed."
              actionLabel="Reset Search Filters"
              onAction={() => {
                setQuery('');
                setDepartment('all');
                setResults([]);
                setSearched(false);
              }}
            />
          </div>
        ) : results.length > 0 ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-semibold text-slate-700">
                Found {totalResults} relevant passages across government resolutions
              </span>
              <span className="text-[11px] text-slate-400">
                Semantically ranked via vector index
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {results.map((res, index) => {
                const docTitle =
                  res.document?.subject ||
                  res.document?.original_filename ||
                  `Resolution Document`;

                return (
                  <div
                    key={`${res.chunk_id}-${index}`}
                    className="bg-white rounded-xl border border-slate-200 p-5 shadow-subtle hover:border-navy-300 hover:shadow-card transition-all"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-2">
                      <div className="flex items-start gap-2.5">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-md bg-navy-900 text-white text-xs font-bold flex-shrink-0 mt-0.5">
                          #{index + 1}
                        </span>
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 leading-snug font-sans">
                            {docTitle}
                          </h4>
                          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 mt-1">
                            {res.document?.gr_number && (
                              <span className="inline-flex items-center gap-1 font-mono text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                                <Bookmark size={11} /> {res.document.gr_number}
                              </span>
                            )}
                            {res.document?.department && <span>• {res.document.department}</span>}
                            {res.section && <span>• Section: {res.section}</span>}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        {res.page !== null && res.page !== undefined && (
                          <span className="px-2 py-0.5 rounded bg-saffron-50 text-saffron-800 border border-saffron-200 text-[10px] font-bold">
                            Page {res.page}
                          </span>
                        )}
                        {getRelevanceBadge(res.score)}
                      </div>
                    </div>

                    {/* Matched Chunk Content */}
                    <div className="mt-3 p-3.5 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-700 leading-relaxed font-sans break-words">
                      "{res.text}"
                    </div>

                    {/* Actions */}
                    <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="text-[11px] text-slate-400 font-mono">
                        Chunk ID: {res.chunk_id}
                      </span>
                      <div className="flex items-center gap-3">
                        <Link
                          to={`/ask`}
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-navy-800 hover:text-navy-900 hover:underline"
                        >
                          <MessageSquareText size={12} />
                          Ask AI about this
                        </Link>
                        <Link
                          to={`/library?id=${res.document_id}`}
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 hover:text-slate-900 hover:underline"
                        >
                          <ExternalLink size={12} />
                          View in Library
                        </Link>
                        <a
                          href={api.getDocumentDownloadUrl(res.document_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 hover:text-emerald-800 hover:underline"
                        >
                          <FileText size={12} />
                          Original PDF
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-subtle text-center">
            <div className="max-w-md mx-auto space-y-2">
              <Sparkles size={24} className="mx-auto text-saffron-500" />
              <h3 className="text-sm font-bold text-slate-900">Search Across All Maharashtra GRs</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-sans">
                Type any keyword, GR number, department name, or topic above. The AI will search across all indexed pages and return matching excerpts.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
