import React, { useState, useRef, useEffect } from 'react';
import { Languages, ChevronDown, Check } from 'lucide-react';
import type { Language } from '../../types';

interface LanguageSelectorProps {
  currentLanguage: Language;
  onLanguageChange: (lang: Language) => void;
}

export const languagesList: { code: Language; label: string; nativeLabel: string }[] = [
  { code: 'mr', label: 'Marathi', nativeLabel: 'मराठी' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिंदी' },
  { code: 'en', label: 'English', nativeLabel: 'English' },
];

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  currentLanguage,
  onLanguageChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeLang = languagesList.find((l) => l.code === currentLanguage) || languagesList[0];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-navy-800/10 shadow-subtle transition-all duration-150"
      >
        <Languages size={15} className="text-saffron-500" />
        <span className="font-semibold text-slate-900">{activeLang.nativeLabel}</span>
        <span className="text-slate-400 text-[11px]">({activeLang.label})</span>
        <ChevronDown size={13} className="text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-44 origin-top-right rounded-lg bg-white border border-slate-200 shadow-elevated z-50 py-1 divide-y divide-slate-100">
          <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Select Language / भाषा निवडा
          </div>
          <div className="py-1">
            {languagesList.map((lang) => {
              const isSelected = lang.code === currentLanguage;
              return (
                <button
                  key={lang.code}
                  onClick={() => {
                    onLanguageChange(lang.code);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 transition-colors ${
                    isSelected ? 'bg-navy-50/70 text-navy-900 font-semibold' : 'text-slate-700'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-slate-900">{lang.nativeLabel}</span>
                    <span className="text-[10px] text-slate-400">{lang.label}</span>
                  </div>
                  {isSelected && <Check size={14} className="text-saffron-600" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
