'use client';

import { useState, useEffect } from 'react';
import { X, Loader, Eye, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface PreviewModalProps {
  epubKey: string;
  targetLang: string;
  targetLangName: string;
  onContinue: () => void;
  onClose: () => void;
}

interface PreviewResponse {
  preview_html: string;
  word_count: number;
  provider: string;
  model: string;
}

export default function PreviewModal({
  epubKey,
  targetLang,
  targetLangName,
  onContinue,
  onClose
}: PreviewModalProps) {
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    generatePreview();
  }, []);

  async function generatePreview() {
    try {
      setLoading(true);
      setError(null);

      const data = await api.generatePreview(epubKey, targetLang, 250);
      console.log(`✅ Preview generated using: ${data.provider}/${data.model}`);
      setPreview(data);
    } catch (err) {
      console.error('Preview generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-200 bg-gradient-to-r from-primary-50 to-accent-50">
          <div className="flex items-center space-x-3">
            <Eye className="w-6 h-6 text-primary-600" />
            <div>
              <h3 className="text-xl font-bold text-neutral-900">Translation Preview</h3>
              <p className="text-sm text-neutral-600">
                First ~250 words translated to {targetLangName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-white rounded-lg transition-colors"
            title="Close preview"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader className="w-12 h-12 text-primary-600 animate-spin mb-4" />
              <p className="text-lg font-semibold text-neutral-900">Generating Preview...</p>
              <p className="text-sm text-neutral-600 mt-2">
                Translating first 250 words with AI
              </p>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center justify-center py-20">
              <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
              <p className="text-lg font-semibold text-neutral-900 mb-2">Preview Failed</p>
              <p className="text-sm text-neutral-600 mb-4">{error}</p>
              <button
                onClick={generatePreview}
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
              </div>

              {/* Preview iframe */}
              <div className="border-2 border-neutral-200 rounded-lg overflow-hidden shadow-inner bg-white">
                <iframe
                  srcDoc={preview.preview_html}
                  className="w-full h-[500px]"
                  sandbox="allow-same-origin"
                  title="Translation Preview"
                />
              </div>

              {/* Info message */}
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>Note:</strong> This preview shows the translation quality. The full book will be
                  translated with the same quality using our production AI models.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {preview && !loading && (
          <div className="flex items-center justify-between p-6 border-t border-neutral-200 bg-neutral-50">
            <button
              onClick={onClose}
              className="btn-secondary"
            >
              Change Language
            </button>
            <button
              onClick={onContinue}
              className="btn-primary btn-large"
            >
              Continue to Payment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
