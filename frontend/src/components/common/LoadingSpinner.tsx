import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
  label?: string;
  size?: number;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  label = 'Loading data...',
  size = 24,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 gap-3 text-slate-500">
      <Loader2 size={size} className="animate-spin text-navy-800" />
      {label && <p className="text-xs font-medium text-slate-500">{label}</p>}
    </div>
  );
};
