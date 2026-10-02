import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquareText,
  Search,
  BookOpen,
  UploadCloud,
  Settings,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react';

interface SidebarProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onClose }) => {
  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      marathiLabel: 'मुख्यपृष्ठ',
      icon: LayoutDashboard,
    },
    {
      to: '/ask',
      label: 'Ask AI',
      marathiLabel: 'एआय प्रश्नोत्तरे',
      icon: MessageSquareText,
      badge: 'Multilingual',
    },
    {
      to: '/search',
      label: 'Semantic Search',
      marathiLabel: 'अर्थपूर्ण शोध',
      icon: Search,
    },
    {
      to: '/library',
      label: 'Document Library',
      marathiLabel: 'जी.आर. भांडार',
      icon: BookOpen,
    },
    {
      to: '/upload',
      label: 'Upload GR',
      marathiLabel: 'जी.आर. अपलोड',
      icon: UploadCloud,
    },
    {
      to: '/settings',
      label: 'Settings',
      marathiLabel: 'सेटिंग्ज',
      icon: Settings,
    },
  ];

  const renderContent = (isMobile: boolean = false) => (
    <div className="flex flex-col h-full bg-navy-950 text-slate-300 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-navy-800/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-navy-800 via-navy-900 to-navy-950 border border-slate-700/60 flex items-center justify-center relative overflow-hidden shadow-sm">
            <span className="text-saffron-500 font-extrabold text-base font-sans">म</span>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-saffron-500 via-white to-emerald-500 opacity-80" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-base font-bold text-white tracking-tight">MAHA-GR</h1>
              <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-saffron-500/20 text-saffron-300 border border-saffron-500/30">
                RAG
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">शासन निर्णय AI सहायक</p>
          </div>
        </div>
        {isMobile && onClose && (
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-navy-900 transition-colors"
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* AI for Bharat Badge */}
      <div className="px-5 pt-3.5 pb-1">
        <div className="px-2.5 py-1.5 rounded-lg bg-navy-900/80 border border-navy-700/50 flex items-center gap-2">
          <Sparkles size={12} className="text-saffron-400 flex-shrink-0" />
          <span className="text-[10px] text-slate-300 font-medium leading-none">
            AI for Bharat • Marathi First
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Core Modules / मुख्य विभाग
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={isMobile && onClose ? onClose : undefined}
              className={({ isActive }) =>
                `group flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-navy-800 text-white font-semibold border-l-4 border-saffron-500 shadow-sm'
                    : 'text-slate-300 hover:bg-navy-900/60 hover:text-white'
                }`
              }
            >
              <div className="flex items-center gap-3 min-w-0">
                <Icon size={17} className="flex-shrink-0 text-slate-400 group-hover:text-saffron-400 transition-colors" />
                <div className="flex flex-col">
                  <span className="truncate">{item.label}</span>
                  <span className="text-[10px] text-slate-400 font-normal leading-tight">
                    {item.marathiLabel}
                  </span>
                </div>
              </div>
              {item.badge && (
                <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Status / Footer */}
      <div className="p-4 border-t border-navy-800/80 bg-navy-950/70">
        <div className="rounded-lg bg-navy-900/90 p-3 border border-navy-800 text-[11px] text-slate-400 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-300 font-medium flex items-center gap-1.5">
              <ShieldCheck size={13} className="text-emerald-400" />
              Grounded AI
            </span>
            <span className="text-[10px] text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
              Verified
            </span>
          </div>
          <p className="text-[10px] text-slate-400 leading-snug">
            Evidence cited strictly from Maharashtra GR records with page references.
          </p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 flex-col flex-shrink-0 border-r border-navy-800/60">
        {renderContent(false)}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
            onClick={onClose}
            aria-hidden="true"
          />
          {/* Drawer */}
          <div className="fixed inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl z-50">
            {renderContent(true)}
          </div>
        </div>
      )}
    </>
  );
};
