'use client';

import { useState } from 'react';
import { BookOpen, Zap, Globe, Shield } from 'lucide-react';
import FileDrop from '@/components/FileDrop';
import PriceBox from '@/components/PriceBox';
import { api } from '@/lib/api';

type Step = 'upload' | 'estimate' | 'processing';

export default function HomePage() {
  const [step, setStep] = useState<Step>('upload');
  const [uploadKey, setUploadKey] = useState<string>('');
  const [estimate, setEstimate] = useState<{ tokens_est: number; price_cents: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleFileSelected = async (file: File) => {
    setIsLoading(true);
    setError('');

    try {
      // Step 1: Get presigned upload URL
      const { key, upload_url } = await api.presignUpload(file.name);
      
      // Step 2: Upload file to R2
      await api.uploadFile(upload_url, file);
      
      // Step 3: Get price estimate
      const estimateResponse = await api.getEstimate(key, 'es'); // Default to Spanish for estimate
      
      setUploadKey(key);
      setEstimate(estimateResponse);
      setStep('estimate');
      
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePayment = async (email: string, targetLang: string) => {
    if (!estimate || !uploadKey) return;

    try {
      const { checkout_url } = await api.createCheckout(
        uploadKey,
        targetLang,
        email,
        estimate.price_cents
      );
      
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
      
    } catch (err) {
      console.error('Payment creation failed:', err);
      throw new Error('Failed to create payment session. Please try again.');
    }
  };

  const resetForm = () => {
    setStep('upload');
    setUploadKey('');
    setEstimate(null);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-3">
            <BookOpen className="w-8 h-8 text-primary-600" />
            <h1 className="text-2xl font-bold text-gray-900">EPUB Translator</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Translate Your Books to Any Language
          </h2>
          <p className="text-xl text-gray-600 mb-6">
            Professional EPUB translation with AI. Get your book in 3 formats: EPUB, PDF & TXT
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4" />
              <span>Fast AI translation</span>
            </div>
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4" />
              <span>50+ languages</span>
            </div>
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4" />
              <span>No account required</span>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-center">
            {error}
            <button
              onClick={resetForm}
              className="ml-4 text-red-600 underline hover:text-red-800"
            >
              Try again
            </button>
          </div>
        )}

        {/* Step Content */}
        <div className="flex flex-col items-center space-y-8">
          {step === 'upload' && (
            <div className="w-full max-w-lg">
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Step 1: Upload Your EPUB
                </h3>
                <p className="text-gray-600">
                  Select your EPUB file to get an instant price estimate
                </p>
              </div>
              <FileDrop 
                onFileSelected={handleFileSelected} 
                disabled={isLoading}
              />
              {isLoading && (
                <div className="text-center mt-4">
                  <p className="text-gray-600">Uploading and analyzing your file...</p>
                </div>
              )}
            </div>
          )}

          {step === 'estimate' && estimate && (
            <div className="w-full max-w-lg">
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Step 2: Choose Language & Pay
                </h3>
                <p className="text-gray-600">
                  Select your target language and proceed with payment
                </p>
              </div>
              <PriceBox
                tokensEst={estimate.tokens_est}
                priceCents={estimate.price_cents}
                onPayment={handlePayment}
              />
              <div className="text-center mt-4">
                <button
                  onClick={resetForm}
                  className="text-gray-500 underline hover:text-gray-700"
                >
                  Upload a different file
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="mt-20 grid md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-6 h-6 text-blue-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Multiple Formats</h4>
            <p className="text-sm text-gray-600">
              Get your translated book in EPUB, PDF, and TXT formats for maximum compatibility
            </p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Zap className="w-6 h-6 text-green-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Fast & Accurate</h4>
            <p className="text-sm text-gray-600">
              Powered by advanced AI models with fallback systems for reliable translations
            </p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Shield className="w-6 h-6 text-purple-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Secure & Private</h4>
            <p className="text-sm text-gray-600">
              Files are automatically deleted after 7 days. No account or personal data required
            </p>
          </div>
        </div>

        {/* Pricing Info */}
        <div className="mt-16 bg-white rounded-lg p-8 border border-gray-200">
          <div className="text-center">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h3>
            <div className="text-3xl font-bold text-primary-600 mb-2">
              $0.30 per 100k characters
            </div>
            <div className="text-gray-600 mb-6">
              $1.00 minimum • No hidden fees • No subscriptions
            </div>
            
            <div className="grid md:grid-cols-2 gap-6 text-left max-w-2xl mx-auto">
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">What you get:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Professional AI translation</li>
                  <li>• EPUB, PDF & TXT formats</li>
                  <li>• Preserved formatting & structure</li>
                  <li>• Email delivery</li>
                </ul>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium text-gray-900">Supported languages:</h4>
                <p className="text-sm text-gray-600">
                  Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, and 40+ more languages
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-20">
        <div className="max-w-4xl mx-auto px-4 py-8 text-center text-gray-500 text-sm">
          <p>© 2024 EPUB Translator. Files auto-delete after 7 days for your privacy.</p>
        </div>
      </footer>
    </div>
  );
}