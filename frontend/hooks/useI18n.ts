import { useState, useEffect, useCallback } from 'react';
import type { ScadaTagI18n } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8100';
const STORAGE_KEY = 'windFarmLang';

export type Lang = 'en' | 'zh';

export const useI18n = () => {
  const [lang, setLangState] = useState<Lang>(
    () => (localStorage.getItem(STORAGE_KEY) as Lang) || 'zh'
  );
  const [tagLabels, setTagLabels] = useState<ScadaTagI18n>({});

  useEffect(() => {
    fetch(`${API_BASE}/api/i18n/tags/all`)
      .then(res => res.json())
      .then(setTagLabels)
      .catch(() => {});
  }, []);

  const setLang = useCallback((newLang: Lang) => {
    setLangState(newLang);
    localStorage.setItem(STORAGE_KEY, newLang);
  }, []);

  const t = useCallback((tagId: string): string => {
    const entry = tagLabels[tagId];
    if (!entry) return tagId;
    return lang === 'zh' ? entry.zh : entry.en;
  }, [tagLabels, lang]);

  // UI labels (non-SCADA)
  const ui = useCallback((en: string, zh: string): string => {
    return lang === 'zh' ? zh : en;
  }, [lang]);

  return { lang, setLang, t, ui };
};
