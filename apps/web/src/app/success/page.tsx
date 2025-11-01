'use client';

import { useSearchParams } from 'next/navigation';
import { BookOpen, Home } from 'lucide-react';
import ProgressPoller from '@/components/ProgressPoller';
import Link from 'next/link';

export default function SuccessPage() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get('job_id');

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-sm border p-8 text-center max-w-md">
          <h1 className="text-xl font-semibold text-gray-900 mb-4">
            Job ID Missing
          </h1>
          <p className="text-gray-600 mb-6">
            No job ID was provided. Please check your payment confirmation email or try uploading again.
          </p>
          <Link
            href="/"
            className="inline-flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BookOpen className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">EPUB Translator</h1>
            </div>
            <Link
              href="/"
              className="text-gray-600 hover:text-gray-800 transition-colors"
            >
              <Home className="w-6 h-6" />
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Payment Successful!
          </h2>
          <p className="text-lg text-gray-600">
            Your translation is being processed. You'll be able to download your book when it's ready.
          </p>
        </div>

        {/* Progress Tracking */}
        <div className="flex justify-center">
          <ProgressPoller jobId={jobId} />
        </div>

        {/* Additional Info */}
        <div className="mt-12 bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-4 text-center">
            What happens next?
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6 text-sm">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Translation Process:</h4>
              <ol className="text-gray-600 space-y-1">
                <li>1. Extracting and analyzing your EPUB</li>
                <li>2. Translating content with AI</li>
                <li>3. Rebuilding EPUB with formatting</li>
                <li>4. Generating PDF and TXT versions</li>
              </ol>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-medium text-gray-900">Download Options:</h4>
              <ul className="text-gray-600 space-y-1">
                <li>• <strong>EPUB:</strong> For e-readers and reading apps</li>
                <li>• <strong>PDF:</strong> For printing or mobile reading</li>
                <li>• <strong>TXT:</strong> Plain text for any device</li>
                <li>• All links expire in 48 hours</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Support Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Translation usually takes 2-5 minutes depending on book size.
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Having issues? Keep this page open and check your email for updates.
          </p>
        </div>
      </main>
    </div>
  );
}