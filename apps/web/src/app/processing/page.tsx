'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import ProgressPoller from '@/components/ProgressPoller';

function ProcessingContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get('job_id');

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid Job ID</h1>
          <p className="text-gray-600 mb-6">No job ID provided in the URL.</p>
          <a 
            href="/"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Return Home
          </a>
        </div>
      </div>
    );
  }

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
                <p className="text-sm text-neutral-600">Made by polyglots, for polyglots</p>
              </div>
            </div>
            <a 
              href="/"
              className="text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Start New Translation
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl md:text-4xl font-bold text-neutral-900 mb-4">
            Your Translation is in Progress
          </h2>
          <p className="text-xl text-neutral-600 max-w-2xl mx-auto">
            We're working on your book translation. This usually takes 2-5 minutes.
          </p>
        </div>

        {/* Progress Component */}
        <div className="flex justify-center">
          <ProgressPoller jobId={jobId} />
        </div>

        {/* Additional Info */}
        <div className="mt-12 bg-white/80 backdrop-blur-sm rounded-xl p-6 border border-neutral-200 shadow-sm max-w-2xl mx-auto">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4 text-center">
            What's happening behind the scenes?
          </h3>
          <div className="space-y-3 text-sm text-neutral-600">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <span className="font-medium">Step 1:</span> Analyzing your EPUB structure and extracting translatable content
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <span className="font-medium">Step 2:</span> AI translation with context preservation and quality checks
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <span className="font-medium">Step 3:</span> Rebuilding EPUB with original formatting and styling
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0"></div>
              <div>
                <span className="font-medium">Step 4:</span> Generating PDF and TXT versions for all your devices
              </div>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
            <p className="text-sm text-green-700 text-center">
              💌 <strong>Email delivery:</strong> Once complete, download links will be sent to your email for easy access.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ProcessingPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <ProcessingContent />
    </Suspense>
  );
}