'use client';

import { useState, useEffect } from 'react';
import { Loader, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface PreviewSectionProps {
  epubKey: string;
  targetLang: string;
  targetLangName: string;
  onLanguageChange: (langCode: string) => void;
}

interface PreviewResponse {
  preview_html: string;
  word_count: number;
  provider: string;
  model: string;
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
  const [progressMessage, setProgressMessage] = useState<string>('🎬 Starting translation...');

  useEffect(() => {
    generatePreview();
  }, [targetLang]);

  function generatePreview() {
    try {
      setLoading(true);
      setError(null);
      setProgressMessage('🎬 Starting translation...');

      console.log('🚀 Starting SSE preview stream for', targetLang);

      // Use SSE streaming for real-time progress updates
      api.streamPreview(
        epubKey,
        targetLang,
        300,
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
        }
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
            Translating first 300 words with AI
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
          <iframe
            srcDoc={preview.preview_html}
            className="w-full flex-1 border-0"
            sandbox="allow-same-origin"
            title="Translation Preview"
          />
        </div>
      )}
    </div>
  );
}
