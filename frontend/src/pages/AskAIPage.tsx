import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send,
  Sparkles,
  Bot,
  User,
  FileText,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  ChevronRight,
  ExternalLink,
  AlertTriangle,
  History,
  X,
  CornerDownLeft,
} from 'lucide-react';
import { api } from '../services/api';
import type { ChatMessage, Citation, Language } from '../types';
import { CitationCard } from '../components/common/CitationCard';

interface AskAIPageProps {
  currentLanguage: Language;
}

interface QueryHistoryItem {
  id: string;
  query: string;
  timestamp: string;
  language: string;
}

export const AskAIPage: React.FC<AskAIPageProps> = ({ currentLanguage }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('all');
  const [chatLanguage, setChatLanguage] = useState<string>('auto');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sessionHistory, setSessionHistory] = useState<QueryHistoryItem[]>(() => {
    try {
      const stored = sessionStorage.getItem('mahagr_session_history');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const samplePrompts = {
    mr: [
      'शेतकरी कर्जमाफी आणि मदत योजनांसंबंधी महत्त्वाचे शासन निर्णय काय आहेत?',
      'शालेय शिक्षण विभागाचे नवीन शैक्षणिक धोरण आणि शुल्क नियमावली सांगा.',
      'आरोग्य विभागाच्या वैद्यकीय भरती व अनुदानाचे नियम कोणते आहेत?',
      'ठिबक सिंचन योजना आणि कृषी अनुदानाचे पात्रता निकष काय आहेत?',
    ],
    hi: [
      'महाराष्ट्र सरकार के किसान राहत और सब्सिडी से संबंधित शासनादेश क्या हैं?',
      'स्कूल शिक्षा विभाग के हाल के नियम और दिशा-निर्देश बताएं।',
      'स्वास्थ्य सेवा और अस्पताल योजनाओं के प्रमुख जी.आर. क्या हैं?',
      'कृषि सब्सिडी और सिंचाई सहायता के लिए क्या पात्रता शर्तें हैं?',
    ],
    en: [
      'What are the key provisions in recent agriculture subsidy government resolutions?',
      'Summarize school education department guidelines regarding fee structure.',
      'What are the eligibility criteria under public health department GRs?',
      'Show resolutions concerning urban infrastructure grants and development.',
    ],
  };

  const effectiveLang: Language = (chatLanguage === 'auto' ? currentLanguage : chatLanguage) as Language;
  const currentPrompts = samplePrompts[effectiveLang] || samplePrompts.mr;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const saveHistoryItem = (queryText: string, lang: string) => {
    const item: QueryHistoryItem = {
      id: `hist-${Date.now()}`,
      query: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      language: lang,
    };
    setSessionHistory((prev) => {
      const updated = [item, ...prev.filter((p) => p.query !== queryText)].slice(0, 15);
      try {
        sessionStorage.setItem('mahagr_session_history', JSON.stringify(updated));
      } catch {}
      return updated;
    });
  };

  const handleSend = async (queryText?: string) => {
    const text = (queryText || inputQuery).trim();
    if (!text || loading) return;

    saveHistoryItem(text, effectiveLang);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      language: effectiveLang,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.askAI({
        query: text,
        language: effectiveLang,
        history,
        department: selectedDepartment === 'all' ? undefined : selectedDepartment,
      });

      const assistantMessage: ChatMessage = {
        id: res.id || `assistant-${Date.now()}`,
        role: 'assistant',
        content: res.content || (res as any).answer || '',
        answer: (res as any).answer || res.content,
        language: res.language || effectiveLang,
        citations: res.citations || [],
        insufficient_evidence: (res as any).insufficient_evidence ?? false,
        timestamp: res.timestamp || new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `क्षमस्व, प्रश्नाचे उत्तर मिळवताना तांत्रिक त्रुटी आली. कृपया खात्री करा की बॅकएंड सेवा सुरू आहे.\n(Error connecting to AI RAG backend: ${
          err?.response?.data?.detail || err.message || 'Server unavailable'
        })`,
        language: effectiveLang,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleReset = () => {
    if (messages.length > 0 && window.confirm('Clear all conversation messages?')) {
      setMessages([]);
      setActiveCitation(null);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-5 h-[calc(100vh-8.5rem)]">
      {/* Session History Sidebar Drawer (Desktop & Mobile) */}
      {historyOpen && (
        <div className="w-full lg:w-64 bg-white rounded-xl border border-slate-200 shadow-subtle p-4 flex flex-col justify-between flex-shrink-0">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                <History size={14} className="text-saffron-600" />
                <span>Session History</span>
              </div>
              <button
                type="button"
                onClick={() => setHistoryOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X size={14} />
              </button>
            </div>

            <div className="mt-3 space-y-1.5 max-h-[60vh] overflow-y-auto">
              {sessionHistory.length === 0 ? (
                <p className="text-xs text-slate-400 italic p-2">No queries in this session yet.</p>
              ) : (
                sessionHistory.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setInputQuery(item.query);
                      setHistoryOpen(false);
                      textareaRef.current?.focus();
                    }}
                    className="w-full text-left p-2 rounded-lg hover:bg-slate-50 border border-transparent hover:border-slate-200 text-xs transition-colors group"
                  >
                    <p className="font-medium text-slate-800 line-clamp-2 leading-snug group-hover:text-navy-900">
                      {item.query}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                      <span>{item.timestamp}</span>
                      <span className="uppercase">{item.language}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {sessionHistory.length > 0 && (
            <button
              onClick={() => {
                setSessionHistory([]);
                sessionStorage.removeItem('mahagr_session_history');
              }}
              className="mt-3 text-[11px] text-slate-400 hover:text-rose-600 text-center py-1 border-t border-slate-100"
            >
              Clear Session Queries
            </button>
          )}
        </div>
      )}

      {/* Main Chat Stream */}
      <div className="flex-1 flex flex-col bg-white rounded-xl border border-slate-200 shadow-subtle overflow-hidden">
        {/* Chat Control Header */}
        <div className="px-5 py-3 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3 bg-white z-10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-navy-900 text-white flex items-center justify-center shadow-sm">
              <Sparkles size={16} className="text-saffron-400" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-slate-900">
                Grounded Multilingual Assistant (एआय सहाय्यक)
              </h2>
              <p className="text-[11px] text-slate-400">
                Strict evidence citations from official Maharashtra GRs
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* History Toggle Button */}
            <button
              type="button"
              onClick={() => setHistoryOpen((prev) => !prev)}
              className={`p-1.5 rounded-lg border text-xs font-medium inline-flex items-center gap-1 transition-colors ${
                historyOpen
                  ? 'bg-navy-50 border-navy-300 text-navy-900'
                  : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
              title="Toggle query history"
            >
              <History size={13} />
              <span className="hidden sm:inline">History</span>
            </button>

            {/* Language Mode Selector */}
            <select
              value={chatLanguage}
              onChange={(e) => setChatLanguage(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-800"
            >
              <option value="auto">Auto-Detect / स्वयं-शोध</option>
              <option value="mr">मराठी (Marathi)</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="en">English</option>
            </select>

            {/* Department Filter */}
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-navy-800"
            >
              <option value="all">All Departments / सर्व विभाग</option>
              <option value="School Education">School Education / शालेय शिक्षण</option>
              <option value="Finance">Finance / वित्त विभाग</option>
              <option value="Agriculture">Agriculture / कृषी व शेतकरी कल्याण</option>
              <option value="Public Health">Public Health / सार्वजनिक आरोग्य</option>
              <option value="Revenue & Forest">Revenue &amp; Forest / महसूल व वन</option>
              <option value="Urban Development">Urban Development / नगर विकास</option>
            </select>

            {messages.length > 0 && (
              <button
                type="button"
                onClick={handleReset}
                title="Clear conversation"
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <RotateCcw size={15} />
              </button>
            )}
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center max-w-xl mx-auto py-8">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-navy-900 to-navy-800 flex items-center justify-center text-white mb-4 shadow-sm">
                <Sparkles size={22} className="text-saffron-400" />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                महाराष्ट्र शासन निर्णय AI सहाय्यक
              </h3>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed font-sans">
                Ask any question regarding Maharashtra Government Resolutions. Answers are generated using Gemini Flash and strictly grounded in official documents stored in Supabase &amp; Pinecone.
              </p>

              {/* Sample Suggestions */}
              <div className="w-full mt-6 space-y-2 text-left">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">
                  Suggested Prompts / सुचवलेले प्रश्न ({effectiveLang.toUpperCase()})
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {currentPrompts.map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(prompt)}
                      className="text-left p-3 rounded-lg border border-slate-200/90 bg-slate-50/70 hover:bg-slate-100 hover:border-slate-300 text-xs text-slate-700 transition-all flex items-center justify-between group"
                    >
                      <span className="line-clamp-1 font-sans">{prompt}</span>
                      <ChevronRight size={14} className="text-slate-400 group-hover:text-navy-900 group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((message) => {
              const isAssistant = message.role === 'assistant';
              return (
                <div
                  key={message.id}
                  className={`flex gap-3 ${isAssistant ? 'justify-start' : 'justify-end'}`}
                >
                  {isAssistant && (
                    <div className="w-7 h-7 rounded-lg bg-navy-900 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot size={15} className="text-saffron-400" />
                    </div>
                  )}

                  <div
                    className={`max-w-2xl rounded-2xl p-4 text-xs ${
                      isAssistant
                        ? 'bg-slate-50 border border-slate-200/80 text-slate-800'
                        : 'bg-navy-900 text-white shadow-subtle'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-4 mb-2 pb-1.5 border-b border-slate-200/50">
                      <span className="text-[10px] font-semibold tracking-wider uppercase opacity-75">
                        {isAssistant ? 'MAHA-GR AI Verified Response' : 'Citizen Query'}
                      </span>
                      {isAssistant && (
                        <button
                          type="button"
                          onClick={() => handleCopy(message.id, message.content)}
                          className="text-[11px] inline-flex items-center gap-1 text-slate-400 hover:text-slate-700 transition-colors"
                        >
                          {copiedId === message.id ? (
                            <>
                              <Check size={12} className="text-emerald-600" />
                              <span className="text-emerald-600 font-medium">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy size={12} />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Insufficient Evidence Warning Banner */}
                    {isAssistant && message.insufficient_evidence && (
                      <div className="mb-3 p-3 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-start gap-2.5">
                        <AlertTriangle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold text-[11px]">
                            अपर्याप्त पुरावा (Insufficient Grounded Evidence)
                          </p>
                          <p className="text-[11px] text-amber-800 mt-0.5 leading-relaxed font-sans">
                            The indexed Maharashtra Government Resolutions do not contain definitive provisions directly answering this query. Answers should not be assumed as official government policy without a verified GR citation.
                          </p>
                        </div>
                      </div>
                    )}

                    <div className="prose prose-sm max-w-none text-xs leading-relaxed font-sans break-words">
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      p: ({ children }) => (
        <p className="mb-2 last:mb-0">{children}</p>
      ),
      strong: ({ children }) => (
        <strong className="font-bold text-slate-900">{children}</strong>
      ),
      ol: ({ children }) => (
        <ol className="list-decimal pl-5 mb-3 space-y-1">
          {children}
        </ol>
      ),
      ul: ({ children }) => (
        <ul className="list-disc pl-5 mb-3 space-y-1">
          {children}
        </ul>
      ),
    }}
  >
    {message.content}
  </ReactMarkdown>
</div>

                    {/* Citations section if present */}
                    {isAssistant && message.citations && message.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-200">
                        <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-700 mb-2">
                          <BookOpen size={13} className="text-saffron-600" />
                          <span>Grounded Evidence &amp; Citations ({message.citations.length})</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {message.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              onClick={() => setActiveCitation(cite)}
                              className="cursor-pointer"
                            >
                              <CitationCard
                                citation={cite}
                                index={cIdx}
                                onPreview={setActiveCitation}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {!isAssistant && (
                    <div className="w-7 h-7 rounded-lg bg-saffron-500 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                      <User size={15} />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-7 h-7 rounded-lg bg-navy-900 text-white flex items-center justify-center flex-shrink-0">
                <Bot size={15} className="text-saffron-400" />
              </div>
              <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 text-xs text-slate-600 flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-navy-800 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-navy-800 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-navy-800 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                <span className="font-medium text-slate-700">
                  पिनेकॉन आणि जी.आर. दस्तावेजांचा शोध घेत आहे (Retrieving evidence &amp; reasoning)...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar with Multi-line Textarea (Enter to submit, Shift+Enter for newline) */}
        <div className="p-3.5 border-t border-slate-200 bg-slate-50/70">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-end gap-2"
          >
            <div className="flex-1 bg-white border border-slate-300 rounded-xl px-3 py-2 shadow-sm focus-within:ring-2 focus-within:ring-navy-900/15 focus-within:border-navy-900 transition-all">
              <textarea
                ref={textareaRef}
                value={inputQuery}
                rows={2}
                onChange={(e) => setInputQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  effectiveLang === 'mr'
                    ? 'महाराष्ट्र शासन निर्णयाबद्दल मराठीत प्रश्न विचारा... (उदा. शेतकरी अनुदान योजना नियम)'
                    : effectiveLang === 'hi'
                    ? 'महाराष्ट्र शासन आदेश के बारे में हिंदी में पूछें... (Shift+Enter for newline)'
                    : 'Ask a question about Maharashtra GRs in English... (Shift+Enter for newline)'
                }
                disabled={loading}
                className="w-full text-xs text-slate-800 placeholder-slate-400 resize-none focus:outline-none bg-transparent font-sans"
              />
              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                <span className="flex items-center gap-1">
                  <CornerDownLeft size={10} /> Enter to send, Shift+Enter for newline
                </span>
                <span>Language: {effectiveLang === 'mr' ? 'मराठी' : effectiveLang === 'hi' ? 'हिंदी' : 'English'}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={!inputQuery.trim() || loading}
              className="h-14 px-4 bg-navy-900 text-white rounded-xl hover:bg-navy-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-sm flex flex-col items-center justify-center gap-1 text-xs font-semibold flex-shrink-0"
            >
              <Send size={15} className="text-saffron-400" />
              <span className="text-[11px]">Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Right Evidence Drawer (Citation Detail Preview) */}
      {activeCitation && (
        <div className="w-full lg:w-80 bg-white rounded-xl border border-slate-200 shadow-subtle p-5 flex flex-col justify-between overflow-y-auto flex-shrink-0">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <FileText size={16} className="text-saffron-600" />
                <h3 className="text-xs font-bold text-slate-900">Cited Evidence Source</h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveCitation(null)}
                className="text-slate-400 hover:text-slate-600 text-xs font-semibold px-2 py-0.5 rounded hover:bg-slate-100"
              >
                Close
              </button>
            </div>

            <div className="mt-4 space-y-3 text-xs">
              <div>
                <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Document Title</div>
                <div className="font-semibold text-slate-800 mt-0.5">{activeCitation.document_title}</div>
              </div>

              {activeCitation.gr_number && (
                <div>
                  <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">GR Number</div>
                  <div className="font-mono text-slate-700 bg-slate-50 px-2 py-1 rounded border border-slate-200/80 mt-0.5 text-[11px]">
                    {activeCitation.gr_number}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Page Number</div>
                  <div className="font-semibold text-slate-800 mt-0.5">Page {activeCitation.page ?? 'N/A'}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Section</div>
                  <div className="font-semibold text-slate-700 mt-0.5 truncate">{activeCitation.section ?? 'General'}</div>
                </div>
              </div>

              <div>
                <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Retrieved Excerpt</div>
                <div className="mt-1.5 p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 text-xs leading-relaxed max-h-56 overflow-y-auto font-sans">
                  "{activeCitation.snippet}"
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-3 border-t border-slate-100 flex flex-col gap-2">
            <a
              href={`/library?id=${activeCitation.document_id}`}
              className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors"
            >
              <ExternalLink size={12} />
              Open Document in Library
            </a>
            <a
              href={api.getDocumentDownloadUrl(activeCitation.document_id)}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 bg-navy-900 hover:bg-navy-800 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <FileText size={12} className="text-saffron-400" />
              Download / Preview PDF
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
