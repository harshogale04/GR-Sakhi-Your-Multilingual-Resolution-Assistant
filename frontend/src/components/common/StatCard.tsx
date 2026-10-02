import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  marathiTitle?: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: string;
  accentColor?: 'navy' | 'saffron' | 'green' | 'blue' | 'amber' | 'rose';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  marathiTitle,
  value,
  icon: Icon,
  description,
  trend,
  accentColor = 'navy',
}) => {
  const colorMap = {
    navy: 'text-navy-900 bg-navy-50 border-navy-100',
    saffron: 'text-saffron-600 bg-saffron-50 border-saffron-100',
    green: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    blue: 'text-sky-600 bg-sky-50 border-sky-100',
    amber: 'text-amber-600 bg-amber-50 border-amber-100',
    rose: 'text-rose-600 bg-rose-50 border-rose-100',
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-subtle hover:shadow-card transition-all duration-200">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-medium text-slate-500">{title}</span>
            {marathiTitle && (
              <span className="text-[11px] text-slate-400">({marathiTitle})</span>
            )}
          </div>
          <p className="text-2xl font-bold tracking-tight text-slate-900">{value}</p>
        </div>
        <div className={`p-2.5 rounded-lg border ${colorMap[accentColor]}`}>
          <Icon size={20} />
        </div>
      </div>
      {(description || trend) && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span>{description}</span>
          {trend && <span className="font-medium text-emerald-600">{trend}</span>}
        </div>
      )}
    </div>
  );
};
