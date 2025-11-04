'use client';

import { useState, useEffect } from 'react';
import { Eye, Loader, CheckCircle, AlertCircle, BookOpen, FileText, Globe } from 'lucide-react';
import { api } from '@/lib/api';
import { LANGUAGES } from '@/lib/languages';
import dynamic from 'next/dynamic';

// Dynamically import EpubReader to avoid SSR issues
const EpubReader = dynamic(() => import('./EpubReader'), { ssr: false });

interface PreviewSectionProps {
  epubKey: string;
  targetLang: string;
  targetLangName: string;
  onLanguageChange: (langCode: string) => void;
}

interface PreviewResponse {
  preview_html?: string;
  preview_url?: string;
  word_count: number;
  provider: string;
  model: string;
  format: string;
}

export default function PreviewSection({
  epubKey,
  targetLang,
  targetLangName,
  onLanguageChange
}: PreviewSectionProps) {
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'html' | 'epub'>('html');

  useEffect(() => {
    generatePreview(viewMode);
  }, [viewMode, targetLang]);

  async function generatePreview(format: 'html' | 'epub') {
    try {
      setLoading(true);
      setError(null);

      const data = await api.generatePreview(epubKey, targetLang, 1500, format);
      console.log(`✅ Preview generated using: ${data.provider}/${data.model}, format: ${format}`);
      setPreview(data);
    } catch (err) {
      console.error('Preview generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm border border-neutral-200 rounded-xl shadow-md overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-50 to-accent-50 border-b border-neutral-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Eye className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-bold text-neutral-900">Translation Preview</h3>
          </div>

          {/* View Mode Toggle */}
          {!loading && (
            <div className="flex items-center space-x-1 bg-white rounded-lg p-1 shadow-sm border border-neutral-200">
              <button
                onClick={() => setViewMode('html')}
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'html'
                    ? 'bg-primary-600 text-white'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
                title="HTML Preview"
              >
                <FileText className="w-4 h-4" />
                <span>HTML</span>
              </button>
              <button
                onClick={() => setViewMode('epub')}
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'epub'
                    ? 'bg-primary-600 text-white'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
                title="EPUB Reader"
              >
                <BookOpen className="w-4 h-4" />
                <span>EPUB</span>
              </button>
            </div>
          )}
        </div>

        <p className="text-sm text-neutral-600">
          First ~1500 words translated to {targetLangName}
        </p>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader className="w-12 h-12 text-primary-600 animate-spin mb-4" />
            <p className="text-lg font-semibold text-neutral-900">Generating Preview...</p>
            <p className="text-sm text-neutral-600 mt-2 text-center">
              Translating first 1500 words with AI - This shows exactly how your final book will look
            </p>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-20">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-lg font-semibold text-neutral-900 mb-2">Preview Failed</p>
            <p className="text-sm text-neutral-600 mb-4">{error}</p>
            <button
              onClick={() => generatePreview(viewMode)}
              className="btn-secondary"
            >
              Try Again
            </button>
          </div>
        )}

        {preview && !loading && (
          <div>
            {/* Preview stats */}
            <div className="flex items-center justify-center space-x-6 mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">
                  {preview.word_count} words translated
                </span>
              </div>
              <div className="text-sm text-neutral-600">
                Model: {preview.provider}/{preview.model}
              </div>
              <div className="text-sm text-neutral-600">
                Mode: {preview.format === 'epub' ? 'E-Reader' : 'HTML'}
              </div>
            </div>

            {/* Preview content */}
            {preview.format === 'epub' && preview.preview_url ? (
              // EPUB Reader mode
              <div className="border-2 border-neutral-200 rounded-lg overflow-hidden shadow-inner bg-neutral-50">
                <EpubReader url={preview.preview_url} className="h-[600px]" />
              </div>
            ) : preview.preview_html ? (
              // HTML iframe mode
              <div className="border-2 border-neutral-200 rounded-lg overflow-hidden shadow-inner bg-white">
                <iframe
                  srcDoc={preview.preview_html}
                  className="w-full h-[600px]"
                  sandbox="allow-same-origin"
                  title="Translation Preview"
                />
              </div>
            ) : null}

            {/* Info message */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-900">
                <strong>Note:</strong> This preview shows the translation quality. The full book will be
                translated with the same quality using our production AI models.
                {preview.format === 'epub' && (
                  <span className="block mt-2">
                    💡 <strong>EPUB mode</strong> shows the exact e-reader experience with pagination.
                  </span>
                )}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
