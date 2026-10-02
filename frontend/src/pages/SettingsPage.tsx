import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Database,
  Cpu,
  Layers,
  CheckCircle2,
  RefreshCw,
  ShieldCheck,
  Languages,
  Info,
  Server,
  Activity,
  AlertCircle,
  FlaskConical,
  Trash2,
} from 'lucide-react';
import { api } from '../services/api';
import type { HealthResponse, Language } from '../types';

interface SettingsPageProps {
  currentLanguage: Language;
  onLanguageChange: (lang: Language) => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  currentLanguage,
  onLanguageChange,
}) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [seedingDemo, setSeedingDemo] = useState(false);
  const [demoMessage, setDemoMessage] = useState<string | null>(null);
  const [resettingDemo, setResettingDemo] = useState(false);

  const checkConnectivity = async () => {
    setChecking(true);
    setError(null);
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } catch {
      setError(
        'Backend server is currently offline or unreachable at http://localhost:8000. Start backend to test live integrations.'
      );
      setHealth(null);
    } finally {
      setChecking(false);
    }
  };

  const handleSeedDemo = async () => {
    setSeedingDemo(true);
    setDemoMessage(null);
    try {
      const result = await api.seedDemo();
      setDemoMessage(result.message || (result.already_seeded ? 'Demo data already loaded.' : `Seeded sample GRs.`));
      await checkConnectivity();
    } catch {
      setDemoMessage('Failed to seed demo data. Is the backend running?');
    } finally {
      setSeedingDemo(false);
    }
  };

  const handleResetDemo = async () => {
    setResettingDemo(true);
    setDemoMessage(null);
    try {
      const result = await api.resetDemo();
      setDemoMessage(result.message || 'Removed demo documents.');
      await checkConnectivity();
    } catch {
      setDemoMessage('Failed to reset demo data. Is the backend running?');
    } finally {
      setResettingDemo(false);
    }
  };

  useEffect(() => {
    checkConnectivity();
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-6">
        <h1 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <SettingsIcon size={20} className="text-saffron-600" />
          System Settings &amp; Diagnostics (प्रणाली सेटिंग्ज)
        </h1>
        <p className="text-xs text-slate-500 mt-1 leading-relaxed font-sans">
          Monitor connectivity across Supabase PostgreSQL, Supabase Storage, Pinecone Vector Database, and Google Gemini AI.
        </p>
      </div>

      {/* Integration Connectivity Status Card with Live / Mock indicator */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Activity size={14} className="text-emerald-600" />
              Infrastructure &amp; AI Integration Status
            </h2>
            <p className="text-[11px] text-slate-400">Live health verification from backend /api/v1/health</p>
          </div>
          <button
            onClick={checkConnectivity}
            disabled={checking}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
          >
            <RefreshCw size={13} className={checking ? 'animate-spin' : ''} />
            Run Diagnostics
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle size={15} className="flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Live / Demo Mode Overview Banner */}
        <div className="p-3.5 rounded-lg bg-navy-50/70 border border-navy-100 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className={`w-2.5 h-2.5 rounded-full ${health ? 'bg-emerald-500 animate-pulse' : 'bg-rose-400'}`} />
            <div>
              <span className="font-bold text-navy-950">
                {health ? 'Backend Server Online' : 'Backend Server Disconnected'}
              </span>
              <p className="text-[11px] text-navy-700 mt-0.5">
                {health?.app_name || 'MAHA-GR Platform'} · Version {health?.version || '1.0.0'}
              </p>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-white text-navy-900 border border-navy-200">
            {health?.services?.supabase_db && health?.services?.pinecone ? 'Production Cloud Mode' : 'Dev / Hybrid Mode'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Supabase DB */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white border border-slate-200 text-navy-900">
                <Database size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">Supabase PostgreSQL</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Tables: documents, chunks</p>
                <span className="text-[10px] text-slate-400 font-mono">Port 5432 / REST</span>
              </div>
            </div>
            {health?.services?.supabase_db ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 size={12} /> Live Cloud
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                Active Mock
              </span>
            )}
          </div>

          {/* Supabase Storage */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white border border-slate-200 text-navy-900">
                <Server size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">Supabase Storage</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Original GR PDF Repository</p>
                <span className="text-[10px] text-slate-400 font-mono">Bucket: government-resolutions</span>
              </div>
            </div>
            {health?.services?.supabase_storage ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 size={12} /> Live Bucket
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                Storage Mock
              </span>
            )}
          </div>

          {/* Pinecone */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white border border-slate-200 text-saffron-600">
                <Layers size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">Pinecone Vector DB</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Index: maha-gr-index (768-dim)</p>
                <span className="text-[10px] text-slate-400 font-mono">Cosine Similarity</span>
              </div>
            </div>
            {health?.services?.pinecone ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 size={12} /> Live Pinecone
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                Vector Fallback
              </span>
            )}
          </div>

          {/* Google Gemini */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-white border border-slate-200 text-emerald-600">
                <Cpu size={18} />
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900">Google Gemini Flash</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">gemini-1.5-flash &amp; gemini-embedding-001</p>
                <span className="text-[10px] text-slate-400 font-mono">Indic Multilingual</span>
              </div>
            </div>
            {health?.services?.gemini_api ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <CheckCircle2 size={12} /> Live Gemini
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
                Simulated AI
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Language Preference Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Languages size={18} className="text-saffron-600" />
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Primary Interface &amp; Q&amp;A Language (प्राधान्य भाषा)
          </h2>
        </div>

        <p className="text-xs text-slate-500 font-sans">
          Select your default operating language. Marathi is the primary official language for Maharashtra Government Resolutions.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { code: 'mr' as Language, name: 'मराठी (Marathi)', desc: 'अधिकृत शासकीय ठराव भाषा' },
            { code: 'hi' as Language, name: 'हिंदी (Hindi)', desc: 'राष्ट्रभाषा संवाद' },
            { code: 'en' as Language, name: 'English', desc: 'Administrative & Researcher access' },
          ].map((lang) => (
            <button
              key={lang.code}
              type="button"
              onClick={() => onLanguageChange(lang.code)}
              className={`p-4 rounded-xl border text-left transition-all ${
                currentLanguage === lang.code
                  ? 'border-navy-900 bg-navy-50/60 ring-2 ring-navy-900/10'
                  : 'border-slate-200 hover:border-slate-300 bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">{lang.name}</span>
                {currentLanguage === lang.code && (
                  <CheckCircle2 size={15} className="text-navy-900" />
                )}
              </div>
              <p className="text-[11px] text-slate-500 mt-1 font-sans">{lang.desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* App Info & Safety Guarantee */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Schema Compliance Note */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-5 space-y-2.5">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <ShieldCheck size={16} className="text-emerald-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Supabase Schema Compliance
            </h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed font-sans">
            MAHA-GR operates strictly within your existing Supabase schema. The <code className="font-mono text-slate-800">documents</code> and <code className="font-mono text-slate-800">chunks</code> tables remain unmodified. The relational <code className="font-mono text-slate-800">chunks</code> table acts as a pointer registry, while raw text is embedded in Pinecone vector metadata.
          </p>
        </div>

        {/* Security & Credentials */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-subtle p-5 space-y-2.5">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <Info size={16} className="text-navy-900" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Security &amp; API Integrity
            </h2>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed font-sans">
            Client requests are routed through the secure FastAPI backend. Supabase Service Role keys, Pinecone API keys, and Gemini AI tokens remain protected on the backend server and are never exposed in browser network payloads.
          </p>
        </div>
      </div>
      {/* Demo Data Management Card */}
      <div className="bg-white rounded-xl border border-amber-200 shadow-subtle p-6 space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-amber-100">
          <FlaskConical size={18} className="text-amber-600" />
          <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Demo Data Management (नमुना डेटा)
          </h2>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed font-sans">
          Load three representative Maharashtra Government Resolutions (Agriculture/Drip Irrigation, School Education/RTE, Public Health/MJPJAY) into the in-memory store for offline demonstration. Demo documents are labeled [नमुना GR] and are never mixed with real uploaded documents.
        </p>

        {demoMessage && (
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
            {demoMessage}
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleSeedDemo}
            disabled={seedingDemo || resettingDemo}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 rounded-lg transition-colors disabled:opacity-50"
          >
            <FlaskConical size={14} />
            {seedingDemo ? 'Seeding…' : 'Seed Demo Data (नमुना GR लोड करा)'}
          </button>
          <button
            onClick={handleResetDemo}
            disabled={seedingDemo || resettingDemo}
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200 rounded-lg transition-colors disabled:opacity-50"
          >
            <Trash2 size={14} />
            {resettingDemo ? 'Clearing…' : 'Reset Demo Data'}
          </button>
        </div>
      </div>

    </div>
  );
};
