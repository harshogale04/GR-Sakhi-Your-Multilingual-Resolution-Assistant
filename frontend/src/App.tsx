import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { AskAIPage } from './pages/AskAIPage';
import { SearchPage } from './pages/SearchPage';
import { LibraryPage } from './pages/LibraryPage';
import { UploadPage } from './pages/UploadPage';
import { SettingsPage } from './pages/SettingsPage';
import type { Language } from './types';

export const App: React.FC = () => {
  const [currentLanguage, setCurrentLanguage] = useState<Language>(() => {
    const saved = localStorage.getItem('mahagr_language') as Language;
    return saved && ['mr', 'hi', 'en'].includes(saved) ? saved : 'mr';
  });

  const handleLanguageChange = (lang: Language) => {
    setCurrentLanguage(lang);
    localStorage.setItem('mahagr_language', lang);
  };

  useEffect(() => {
    document.documentElement.lang = currentLanguage;
  }, [currentLanguage]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout
              currentLanguage={currentLanguage}
              onLanguageChange={handleLanguageChange}
            />
          }
        >
          <Route index element={<DashboardPage />} />
          <Route
            path="ask"
            element={<AskAIPage currentLanguage={currentLanguage} />}
          />
          <Route
            path="search"
            element={<SearchPage currentLanguage={currentLanguage} />}
          />
          <Route path="library" element={<LibraryPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route
            path="settings"
            element={
              <SettingsPage
                currentLanguage={currentLanguage}
                onLanguageChange={handleLanguageChange}
              />
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
