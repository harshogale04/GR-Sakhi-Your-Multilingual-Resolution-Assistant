import React from 'react';
import { Bookmark, ExternalLink } from 'lucide-react';
import type { Citation } from '../../types';

interface CitationCardProps {
  citation: Citation;
  index: number;
  onPreview?: (citation: Citation) => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, index, onPreview }) => {
  return (
    <div className="bg-slate-50 border border-slate-200/90 rounded-lg p-3 text-left hover:border-navy-300 hover:bg-slate-100/70 transition-all duration-150">
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-navy-900 text-white text-[11px] font-bold">
            {index + 1}
          </span>
          <span className="text-xs font-semibold text-slate-800 truncate" title={citation.document_title}>
            {citation.document_title}
          </span>
        </div>
        {citation.page !== undefined && citation.page !== null && (
          <span className="flex-shrink-0 text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-saffron-100 text-saffron-800 border border-saffron-200">
            Page {citation.page}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 text-[11px] text-slate-500 mb-2">
        {citation.gr_number && (
          <span className="inline-flex items-center gap-1">
            <Bookmark size={11} className="text-slate-400" />
            <span className="font-mono">{citation.gr_number}</span>
          </span>
        )}
        {citation.department && (
          <span>• {citation.department}</span>
        )}
        {citation.section && (
          <span>• {citation.section}</span>
        )}
      </div>

      <p className="text-xs text-slate-600 line-clamp-3 bg-white p-2 rounded border border-slate-200/70 font-sans leading-relaxed">
        "{citation.snippet}"
      </p>

      {onPreview && (
        <button
          type="button"
          onClick={() => onPreview(citation)}
          className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-navy-800 hover:text-navy-900 hover:underline"
        >
          <ExternalLink size={11} />
          View full source reference
        </button>
      )}
    </div>
  );
};
