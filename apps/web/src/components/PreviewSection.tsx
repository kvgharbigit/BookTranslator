'use client';

import { useState, useEffect } from 'react';
import { Loader, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface PreviewSectionProps {
  epubKey: string;
  targetLang: string;
  targetLangName: string;
  onLanguageChange: (langCode: string) => void;
  outputFormat?: string;
}

interface PreviewResponse {
  translation_html: string;
  bilingual_html: string;
  word_count: number;
  provider: string;
  model: string;
}

type PreviewTab = 'translation' | 'bilingual';

export default function PreviewSection({
  epubKey,
  targetLang,
  targetLangName,
  onLanguageChange,
  outputFormat = 'translation'
}: PreviewSectionProps) {
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string>('🎬 Starting translation...');
  const [activeTab, setActiveTab] = useState<PreviewTab>('translation');

  // Only regenerate preview when language changes (not when output format changes)
  useEffect(() => {
    generatePreview();
  }, [targetLang]);

  // Automatically switch tab based on selected output format (no regeneration needed)
  useEffect(() => {
    if (outputFormat === 'bilingual' || outputFormat === 'both') {
      setActiveTab('bilingual');
    } else {
      setActiveTab('translation');
    }
  }, [outputFormat]);

  function generatePreview() {
    try {
      setLoading(true);
      setError(null);
      setProgressMessage('🎬 Starting translation...');

      console.log('🚀 Starting SSE preview stream for', targetLang, 'format:', outputFormat);

      // Use SSE streaming for real-time progress updates
      api.streamPreview(
        epubKey,
        targetLang,
        600,
        // onProgress
        (message: string) => {
          console.log('📊 Progress update:', message);
          setProgressMessage(message);
        },
        // onComplete
        (data) => {
          console.log(`✅ Preview generated using: ${data.provider}/${data.model}`);
          setPreview(data);
          setLoading(false);
        },
        // onError
        (errorMsg: string) => {
          console.error('❌ Preview generation error:', errorMsg);
          setError(errorMsg);
          setLoading(false);
        },
        // outputFormat
        outputFormat
      );
    } catch (err) {
      console.error('❌ Preview generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
      setLoading(false);
    }
  }

  return (
    <div className="h-[700px] flex flex-col">

      {loading && (
        <div className="flex flex-col items-center justify-center flex-1 py-20">
          <Loader className="w-12 h-12 text-primary-600 animate-spin mb-4" />
          <p className="text-lg font-semibold text-neutral-900 mb-2">
            {progressMessage}
          </p>
          <p className="text-sm text-neutral-600 text-center">
            Translating first 600 words with AI
          </p>
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center flex-1 py-20">
          <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
          <p className="text-lg font-semibold text-neutral-900 mb-2">Preview Failed</p>
          <p className="text-sm text-neutral-600 mb-4">{error}</p>
          <button
            onClick={() => generatePreview()}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Try Again
          </button>
        </div>
      )}

      {preview && !loading && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tab navigation */}
          <div className="flex space-x-1 border-b border-neutral-200 bg-white px-4">
            <button
              onClick={() => setActiveTab('translation')}
              className={`px-4 py-3 font-medium text-sm transition-colors relative ${
                activeTab === 'translation'
                  ? 'text-primary-600'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              Translation Only
              {activeTab === 'translation' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('bilingual')}
              className={`px-4 py-3 font-medium text-sm transition-colors relative ${
                activeTab === 'bilingual'
                  ? 'text-primary-600'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              Bilingual Reader
              {activeTab === 'bilingual' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-600" />
              )}
            </button>
          </div>

          {/* Preview content */}
          <div className="flex-1 overflow-hidden">
            <iframe
              srcDoc={activeTab === 'translation' ? preview.translation_html : preview.bilingual_html}
              className="w-full h-full border-0"
              sandbox="allow-same-origin"
              title={activeTab === 'translation' ? 'Translation Preview' : 'Bilingual Preview'}
            />
          </div>
        </div>
      )}
    </div>
  );
}
