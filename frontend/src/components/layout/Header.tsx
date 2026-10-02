import React, { useState, useEffect } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { LanguageSelector } from '../common/LanguageSelector';
import type { Language } from '../../types';
import { api } from '../../services/api';
import { Activity, UploadCloud, Menu } from 'lucide-react';

interface HeaderProps {
  currentLanguage: Language;
  onLanguageChange: (lang: Language) => void;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentLanguage,
  onLanguageChange,
  onToggleMobileMenu,
}) => {
  const location = useLocation();
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkStatus = async () => {
      try {
        const health = await api.checkHealth();
        if (isMounted) {
          setBackendOnline(health.status === 'ok');
        }
      } catch {
        if (isMounted) {
          setBackendOnline(false);
        }
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const getPageTitle = (pathname: string) => {
    switch (pathname) {
      case '/':
        return { en: 'Dashboard Overview', mr: 'डॅशबोर्ड आढावा' };
      case '/ask':
        return { en: 'Ask AI (Multilingual RAG)', mr: 'एआय प्रश्नोत्तरे' };
      case '/search':
        return { en: 'Semantic GR Search', mr: 'अर्थपूर्ण शासन निर्णय शोध' };
      case '/library':
        return { en: 'Document Library', mr: 'शासन निर्णय भांडार' };
      case '/upload':
        return { en: 'Upload Government Resolution', mr: 'जी.आर. अपलोड व प्रक्रिया' };
      case '/settings':
        return { en: 'System Settings', mr: 'प्रणाली सेटिंग्ज' };
      default:
        return { en: 'MAHA-GR Platform', mr: 'महाराष्ट्र शासन निर्णय प्रणाली' };
    }
  };

  const titleInfo = getPageTitle(location.pathname);

  return (
    <header className="h-16 bg-white border-b border-slate-200/90 px-6 flex items-center justify-between sticky top-0 z-30 shadow-subtle">
      {/* Title & Page Header */}
      <div className="flex items-center gap-3">
        {onToggleMobileMenu && (
          <button
            type="button"
            onClick={onToggleMobileMenu}
            className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            aria-label="Open navigation menu"
          >
            <Menu size={20} />
          </button>
        )}
        <div>
          <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>{titleInfo.en}</span>
            <span className="text-slate-400 font-normal text-xs hidden sm:inline">/ {titleInfo.mr}</span>
          </h2>
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Backend Status indicator */}
        <div
          className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border bg-slate-50 transition-colors"
          title="FastAPI Backend Health"
        >
          {backendOnline === true ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-emerald-700">API Live</span>
            </>
          ) : backendOnline === false ? (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500" />
              <span className="text-rose-600">API Offline</span>
            </>
          ) : (
            <>
              <Activity size={12} className="text-slate-400 animate-spin" />
              <span className="text-slate-500">Checking API</span>
            </>
          )}
        </div>

        {/* Language Selector */}
        <LanguageSelector
          currentLanguage={currentLanguage}
          onLanguageChange={onLanguageChange}
        />

        {/* Quick Upload Action */}
        <Link
          to="/upload"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-navy-900 text-white rounded-lg text-xs font-semibold hover:bg-navy-800 shadow-sm transition-colors"
        >
          <UploadCloud size={14} className="text-saffron-400" />
          <span>Upload GR</span>
        </Link>
      </div>
    </header>
  );
};
