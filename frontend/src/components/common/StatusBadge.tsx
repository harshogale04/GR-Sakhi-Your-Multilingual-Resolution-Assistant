import React from 'react';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';

interface StatusBadgeProps {
  status: 'PROCESSING' | 'COMPLETED' | 'INDEXED' | 'FAILED' | string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toUpperCase();

  const isSmall = size === 'sm';
  const sizeClasses = isSmall ? 'text-xs px-2 py-0.5' : 'text-xs font-medium px-2.5 py-1';
  const iconSize = isSmall ? 12 : 14;

  switch (normalized) {
    case 'COMPLETED':
    case 'INDEXED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 ${sizeClasses}`}
        >
          <CheckCircle2 size={iconSize} className="text-emerald-600" />
          {normalized === 'COMPLETED' ? 'Completed' : 'Indexed'}
        </span>
      );
    case 'PROCESSING':
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200/80 ${sizeClasses}`}
        >
          <Clock size={iconSize} className="animate-spin text-amber-600" />
          Processing
        </span>
      );
    case 'FAILED':
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200/80 ${sizeClasses}`}
        >
          <AlertCircle size={iconSize} className="text-rose-600" />
          Failed
        </span>
      );
    default:
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 ${sizeClasses}`}
        >
          {status}
        </span>
      );
  }
};
