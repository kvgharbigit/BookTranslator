'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, Download, AlertCircle, Loader2, FileText, BookOpen, Image } from 'lucide-react';
import { api, JobStatusResponse } from '@/lib/api';

interface ProgressPollerProps {
  jobId: string;
}

const PROGRESS_STEPS = {
  queued: { label: 'Payment confirmed, queuing translation...', progress: 10 },
  unzipping: { label: 'Step 1/4: Extracting EPUB content...', progress: 25 },
  segmenting: { label: 'Step 1/4: Analyzing document structure...', progress: 30 },
  translating: { label: 'Step 2/4: Translating chapters...', progress: 60 },
  assembling: { label: 'Step 3/4: Rebuilding EPUB...', progress: 80 },
  uploading: { label: 'Step 4/4: Preparing download...', progress: 95 },
  done: { label: 'Translation complete!', progress: 100 },
};

export default function ProgressPoller({ jobId }: ProgressPollerProps) {
  const [job, setJob] = useState<JobStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let pollCount = 0;
    const maxPolls = 120; // 10 minutes max (5s intervals)

    const pollJobStatus = async () => {
      try {
        const jobStatus = await api.getJobStatus(jobId);
        setJob(jobStatus);
        setError(null);

        // Stop polling if job is complete or failed
        if (jobStatus.status === 'done' || jobStatus.status === 'failed') {
          clearInterval(interval);
        }

        pollCount++;
        if (pollCount >= maxPolls) {
          clearInterval(interval);
          setError('Polling timeout. Please refresh the page to check status.');
        }
      } catch (err) {
        console.error('Failed to poll job status:', err);
        setError('Failed to check job status. Please refresh the page.');
        clearInterval(interval);
      }
    };

    // Initial poll
    pollJobStatus();

    // Set up polling interval (every 5 seconds)
    interval = setInterval(pollJobStatus, 5000);

    return () => clearInterval(interval);
  }, [jobId]);

  if (error) {
    return (
      <div className="w-full max-w-md mx-auto bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-red-900">Error</h3>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="w-full max-w-md mx-auto bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-primary-500" />
          <span className="text-gray-600">Loading job status...</span>
        </div>
      </div>
    );
  }

  const currentStep = PROGRESS_STEPS[job.progress_step as keyof typeof PROGRESS_STEPS] ||
                     { label: job.progress_step, progress: 50 };

  // Use actual progress_percent if available (0-100), otherwise fall back to step-based progress
  const progressPercent = job.progress_percent || currentStep.progress;

  if (job.status === 'failed') {
    return (
      <div className="w-full max-w-md mx-auto bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-4">
          <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-red-900">Translation Failed</h3>
            <p className="text-sm text-red-700">
              {job.error || 'An error occurred during translation.'}
            </p>
          </div>
        </div>
        <p className="text-sm text-gray-600">
          Please try again or contact support if the problem persists.
        </p>
      </div>
    );
  }

  if (job.status === 'done' && job.download_urls) {
    return (
      <div className="w-full max-w-md mx-auto bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center space-x-3 mb-6">
          <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-green-900">Translation Complete!</h3>
            <p className="text-sm text-green-700">Your book is ready for download</p>
          </div>
        </div>

        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-900 mb-3">
            Choose your preferred format:
          </p>

          {/* EPUB Download */}
          {job.download_urls.epub && (
            <a
              href={job.download_urls.epub}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors group"
            >
              <BookOpen className="w-6 h-6 text-blue-600" />
              <div className="flex-1">
                <p className="font-medium text-blue-900">EPUB</p>
                <p className="text-sm text-blue-700">For e-readers (Kindle, Apple Books)</p>
              </div>
              <Download className="w-5 h-5 text-blue-600 group-hover:translate-y-0.5 transition-transform" />
            </a>
          )}

          {/* PDF Download */}
          {job.download_urls.pdf && (
            <a
              href={job.download_urls.pdf}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors group"
            >
              <Image className="w-6 h-6 text-purple-600" />
              <div className="flex-1">
                <p className="font-medium text-purple-900">PDF</p>
                <p className="text-sm text-purple-700">For printing or mobile reading</p>
              </div>
              <Download className="w-5 h-5 text-purple-600 group-hover:translate-y-0.5 transition-transform" />
            </a>
          )}

          {/* TXT Download */}
          {job.download_urls.txt && (
            <a
              href={job.download_urls.txt}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors group"
            >
              <FileText className="w-6 h-6 text-green-600" />
              <div className="flex-1">
                <p className="font-medium text-green-900">TXT</p>
                <p className="text-sm text-green-700">Plain text for any device</p>
              </div>
              <Download className="w-5 h-5 text-green-600 group-hover:translate-y-0.5 transition-transform" />
            </a>
          )}

          {/* Bilingual EPUB Download */}
          {job.download_urls.bilingual_epub && (
            <a
              href={job.download_urls.bilingual_epub}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors group"
            >
              <BookOpen className="w-6 h-6 text-indigo-600" />
              <div className="flex-1">
                <p className="font-medium text-indigo-900">EPUB (Bilingual)</p>
                <p className="text-sm text-indigo-700">Translation with original text as subtitles</p>
              </div>
              <Download className="w-5 h-5 text-indigo-600 group-hover:translate-y-0.5 transition-transform" />
            </a>
          )}

          {/* Bilingual PDF Download */}
          {job.download_urls.bilingual_pdf && (
            <a
              href={job.download_urls.bilingual_pdf}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-pink-50 border border-pink-200 rounded-lg hover:bg-pink-100 transition-colors group"
            >
              <Image className="w-6 h-6 text-pink-600" />
              <div className="flex-1">
                <p className="font-medium text-pink-900">PDF (Bilingual)</p>
                <p className="text-sm text-pink-700">Translation with original text as subtitles</p>
              </div>
              <Download className="w-5 h-5 text-pink-600 group-hover:translate-y-0.5 transition-transform" />
            </a>
          )}

          {/* Bilingual TXT Download */}
          {job.download_urls.bilingual_txt && (
            <a
              href={job.download_urls.bilingual_txt}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-3 p-3 bg-teal-50 border border-teal-200 rounded-lg hover:bg-teal-100 transition-colors group"
            >
              <FileText className="w-6 h-6 text-teal-600" />
              <div className="flex-1">
                <p className="font-medium text-teal-900">TXT (Bilingual)</p>
                <p className="text-sm text-teal-700">Translation with original text as subtitles</p>
              </div>
              <Download className="w-5 h-5 text-teal-600 group-hover:translate-y-0.5 transition-transform" />
            </a>
          )}
        </div>

        <p className="text-xs text-gray-500 mt-4 text-center">
          ⚠️ Download these files soon - they will be automatically deleted after 5 days
        </p>
        {job.expires_at && (
          <p className="text-xs text-gray-400 mt-1 text-center">
            Files expire: {new Date(job.expires_at).toLocaleDateString()}
          </p>
        )}
      </div>
    );
  }

  // Show progress for in-progress jobs
  return (
    <div className="w-full max-w-md mx-auto bg-white border border-gray-200 rounded-lg p-6">
      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <Loader2 className="w-6 h-6 animate-spin text-primary-500 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-gray-900">Translating Your Book</h3>
            <p className="text-sm text-gray-600">{currentStep.label}</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-500 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Progress Percentage */}
        <div className="text-center">
          <p className="text-lg font-semibold text-primary-600">
            {progressPercent}%
          </p>
        </div>

        <div className="text-center mt-2">
          <p className="text-sm text-gray-500">
            This usually takes 2-5 minutes
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Job ID: {jobId.slice(0, 8)}...
          </p>
        </div>
      </div>
    </div>
  );
}