'use client';

import { useState } from 'react';
import { Search, BookOpen, Image, FileText, Download, AlertCircle, Loader2, CheckCircle, Clock } from 'lucide-react';

interface Job {
  id: string;
  status: string;
  progress_step: string;
  progress_percent: number;
  created_at: string;
  download_urls?: {
    epub?: string;
    pdf?: string;
    txt?: string;
    bilingual_epub?: string;
    bilingual_pdf?: string;
    bilingual_txt?: string;
  };
  expires_at?: string;
  error?: string;
  output_format?: string;
}

export default function RetrievePage() {
  const [email, setEmail] = useState('');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(false);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE;
      if (!apiBase) {
        throw new Error('API configuration missing');
      }
      const response = await fetch(`${apiBase}/jobs-by-email/${encodeURIComponent(email)}`);

      if (!response.ok) {
        throw new Error('Failed to fetch jobs');
      }

      const data = await response.json();
      setJobs(data);
      setSearched(true);
    } catch (err) {
      console.error('Failed to fetch jobs:', err);
      setError('Failed to retrieve translations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-neutral-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-primary-500 to-purple-500 rounded-xl shadow-sm">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6 text-white">
                  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                  EPUB Translator
                </h1>
                <p className="text-sm text-neutral-600">Retrieve Your Translations</p>
              </div>
            </div>
            <a
              href="/"
              className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
            >
              ← Back to Home
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
            Retrieve Your Downloads
          </h2>
          <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
            Enter your email to access all your translations from the last 5 days
          </p>
        </div>

        {/* Search Form */}
        <div className="max-w-md mx-auto mb-12">
          <form onSubmit={handleSearch} className="flex flex-col space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full px-4 py-3 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-3 px-6 rounded-lg font-medium hover:from-primary-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  <span>Retrieve Translations</span>
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </div>

        {/* Results */}
        {searched && (
          <div className="space-y-6">
            {jobs.length === 0 ? (
              <div className="text-center py-12 bg-white/80 backdrop-blur-sm rounded-xl border border-neutral-200">
                <AlertCircle className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                  No Translations Found
                </h3>
                <p className="text-neutral-600">
                  We couldn't find any translations for this email address in the last 5 days.
                </p>
              </div>
            ) : (
              <>
                <h3 className="text-2xl font-bold text-neutral-900">
                  Your Translations ({jobs.length})
                </h3>

                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className="bg-white/80 backdrop-blur-sm rounded-xl border border-neutral-200 p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center space-x-3 mb-2">
                          {job.status === 'done' && (
                            <CheckCircle className="w-5 h-5 text-green-500" />
                          )}
                          {job.status === 'processing' && (
                            <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                          )}
                          {job.status === 'failed' && (
                            <AlertCircle className="w-5 h-5 text-red-500" />
                          )}
                          <span className="text-sm font-medium text-neutral-900 capitalize">
                            {job.status === 'done' ? 'Completed' : job.status}
                          </span>
                        </div>
                        <p className="text-xs text-neutral-500">
                          Job ID: {job.id.slice(0, 13)}...
                        </p>
                        <p className="text-xs text-neutral-500 flex items-center space-x-1 mt-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(job.created_at).toLocaleString()}</span>
                        </p>
                      </div>

                      {job.status === 'done' && job.expires_at && (
                        <div className="text-right">
                          <p className="text-xs text-neutral-500">Expires:</p>
                          <p className="text-xs font-medium text-orange-600">
                            {new Date(job.expires_at).toLocaleDateString()}
                          </p>
                        </div>
                      )}
                    </div>

                    {job.status === 'done' && job.download_urls && (
                      <div className="space-y-3 mt-4">
                        <p className="text-sm font-medium text-neutral-700 mb-2">
                          Download Files
                          {job.output_format && (
                            <span className="ml-2 text-xs text-neutral-500">
                              ({job.output_format === 'both' ? '6 files' : '3 files'})
                            </span>
                          )}
                        </p>

                        {/* Regular translation files */}
                        {(job.download_urls.epub || job.download_urls.pdf || job.download_urls.txt) && (
                          <div className="space-y-2">
                            {(job.output_format === 'both' || job.output_format === 'bilingual') && (
                              <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mt-2">
                                Translation Only
                              </p>
                            )}

                            {job.download_urls.epub && (
                              <a
                                href={job.download_urls.epub}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors group"
                              >
                                <BookOpen className="w-5 h-5 text-blue-600" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-blue-900">EPUB</p>
                                </div>
                                <Download className="w-4 h-4 text-blue-600 group-hover:translate-y-0.5 transition-transform" />
                              </a>
                            )}

                            {job.download_urls.pdf && (
                              <a
                                href={job.download_urls.pdf}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center space-x-3 p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors group"
                              >
                                <Image className="w-5 h-5 text-purple-600" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-purple-900">PDF</p>
                                </div>
                                <Download className="w-4 h-4 text-purple-600 group-hover:translate-y-0.5 transition-transform" />
                              </a>
                            )}

                            {job.download_urls.txt && (
                              <a
                                href={job.download_urls.txt}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors group"
                              >
                                <FileText className="w-5 h-5 text-green-600" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-green-900">TXT</p>
                                </div>
                                <Download className="w-4 h-4 text-green-600 group-hover:translate-y-0.5 transition-transform" />
                              </a>
                            )}
                          </div>
                        )}

                        {/* Bilingual files */}
                        {(job.download_urls.bilingual_epub || job.download_urls.bilingual_pdf || job.download_urls.bilingual_txt) && (
                          <div className="space-y-2">
                            <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mt-3">
                              Bilingual (with subtitles)
                            </p>

                            {job.download_urls.bilingual_epub && (
                              <a
                                href={job.download_urls.bilingual_epub}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors group"
                              >
                                <BookOpen className="w-5 h-5 text-blue-600" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-blue-900">EPUB (Bilingual)</p>
                                </div>
                                <Download className="w-4 h-4 text-blue-600 group-hover:translate-y-0.5 transition-transform" />
                              </a>
                            )}

                            {job.download_urls.bilingual_pdf && (
                              <a
                                href={job.download_urls.bilingual_pdf}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center space-x-3 p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors group"
                              >
                                <Image className="w-5 h-5 text-purple-600" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-purple-900">PDF (Bilingual)</p>
                                </div>
                                <Download className="w-4 h-4 text-purple-600 group-hover:translate-y-0.5 transition-transform" />
                              </a>
                            )}

                            {job.download_urls.bilingual_txt && (
                              <a
                                href={job.download_urls.bilingual_txt}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors group"
                              >
                                <FileText className="w-5 h-5 text-green-600" />
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-green-900">TXT (Bilingual)</p>
                                </div>
                                <Download className="w-4 h-4 text-green-600 group-hover:translate-y-0.5 transition-transform" />
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {job.status === 'processing' && (
                      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                        <p className="text-sm text-blue-700">
                          This translation is still in progress ({job.progress_percent}%)
                        </p>
                      </div>
                    )}

                    {job.status === 'failed' && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-700">
                          {job.error || 'Translation failed. Please try again.'}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
