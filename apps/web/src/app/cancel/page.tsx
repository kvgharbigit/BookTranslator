'use client';

import { BookOpen, Home, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function CancelPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-100">
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
      <main className="max-w-4xl mx-auto px-4 py-16">
        <div className="text-center">
          <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <ArrowLeft className="w-10 h-10 text-orange-600" />
          </div>
          
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Payment Cancelled
          </h2>
          
          <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
            No worries! Your payment was cancelled and you haven't been charged anything.
          </p>

          <div className="space-y-4">
            <Link
              href="/"
              className="inline-flex items-center space-x-2 bg-primary-600 text-white px-6 py-3 rounded-md font-medium hover:bg-primary-700 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Try Again</span>
            </Link>
          </div>

          {/* Help Section */}
          <div className="mt-16 bg-white rounded-lg p-8 border border-gray-200 max-w-2xl mx-auto">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Need Help?
            </h3>
            
            <div className="text-left space-y-4 text-gray-600">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Common reasons for cancellation:</h4>
                <ul className="text-sm space-y-1">
                  <li>• Changed your mind about the translation</li>
                  <li>• Wanted to upload a different file</li>
                  <li>• Payment method issues</li>
                  <li>• Accidentally closed the payment window</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">What you can do:</h4>
                <ul className="text-sm space-y-1">
                  <li>• Go back and upload your EPUB file again</li>
                  <li>• Try a different payment method if needed</li>
                  <li>• Contact support if you're experiencing technical issues</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Pricing Reminder */}
          <div className="mt-8">
            <p className="text-sm text-gray-500">
              Remember: Translation costs just $0.30 per 100k characters (minimum $1.00)
            </p>
            <p className="text-sm text-gray-500">
              You get EPUB + PDF + TXT formats with no hidden fees
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}