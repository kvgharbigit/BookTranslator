'use client';

import { useState } from 'react';
import { BookOpen, Zap, Globe, Shield, Sparkles, ArrowRight } from 'lucide-react';
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-neutral-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-purple-500 rounded-xl shadow-sm">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">EPUB Translator</h1>
              <p className="text-sm text-neutral-600">Made by polyglots, for polyglots</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-neutral-900 mb-4">
            Upload. Translate.
            <span className="bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent block">Download.</span>
          </h2>
          <p className="text-xl text-neutral-600 mb-4 max-w-2xl mx-auto">
            No account needed. No subscription. Just upload your EPUB and get it translated to any language.
          </p>
          <div className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 rounded-full text-sm font-semibold mb-8">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
            Best prices on the market • 100% transparent pricing
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-neutral-700 font-medium">Fast AI translation</span>
            </div>
            <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm">
              <Globe className="w-4 h-4 text-blue-500" />
              <span className="text-neutral-700 font-medium">50+ languages</span>
            </div>
            <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-full shadow-sm">
              <Shield className="w-4 h-4 text-green-500" />
              <span className="text-neutral-700 font-medium">No account required</span>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-6 bg-gradient-to-r from-red-50 to-pink-50 border border-red-200 rounded-xl text-red-700 text-center shadow-sm">
            <div className="flex items-center justify-center space-x-2 mb-2">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="font-medium">Something went wrong</span>
            </div>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={resetForm}
              className="inline-flex items-center px-4 py-2 bg-white text-red-600 rounded-lg hover:bg-red-50 transition-colors shadow-sm"
            >
              <ArrowRight className="w-4 h-4 mr-2 rotate-180" />
              Try again
            </button>
          </div>
        )}

        {/* Step Content */}
        <div className="flex flex-col items-center space-y-8">
          {step === 'upload' && (
            <div className="w-full max-w-lg">
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                  Step 1: Upload Your EPUB
                </h3>
                <p className="text-neutral-600">
                  Select your EPUB file to get an instant price estimate
                </p>
              </div>
              <FileDrop 
                onFileSelected={handleFileSelected} 
                disabled={isLoading}
                maxSizeMB={50}
              />
              {isLoading && (
                <div className="text-center mt-6">
                  <div className="inline-flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-primary-50 to-blue-50 rounded-full border border-primary-200">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary-600 border-t-transparent"></div>
                    <p className="text-primary-700 font-medium">Uploading and analyzing your file...</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {step === 'estimate' && estimate && (
            <div className="w-full max-w-lg">
              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                  Step 2: Choose Language & Pay
                </h3>
                <p className="text-neutral-600">
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
                  className="text-neutral-500 underline hover:text-neutral-700"
                >
                  Upload a different file
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="mt-20 grid md:grid-cols-3 gap-6">
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <BookOpen className="w-7 h-7 text-white" />
            </div>
            <h4 className="font-semibold text-neutral-900 mb-2">Multiple Formats</h4>
            <p className="text-sm text-neutral-600">
              Get your translated book in EPUB, PDF, and TXT formats
            </p>
          </div>
          
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
            <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h4 className="font-semibold text-neutral-900 mb-2">Fast & Simple</h4>
            <p className="text-sm text-neutral-600">
              Upload your file and get professional translation in minutes
            </p>
          </div>
          
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h4 className="font-semibold text-neutral-900 mb-2">No Strings Attached</h4>
            <p className="text-sm text-neutral-600">
              No account, no subscription, no personal data required
            </p>
          </div>
        </div>

        {/* Pricing Info */}
        <div className="mt-16 bg-white/80 backdrop-blur-sm rounded-xl p-8 border border-neutral-200 shadow-sm">
          <div className="text-center">
            <div className="text-center mb-6">
              <div className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-yellow-100 to-orange-100 text-orange-700 rounded-full text-sm font-medium mb-3">
                🏆 Best Value on the Market
              </div>
              <h3 className="text-2xl font-bold text-neutral-900 mb-3">
                Fair, Transparent Pricing
              </h3>
              <p className="text-neutral-600 mb-4">
                Created by language lovers who understand the real cost of quality translation.
              </p>
              <p className="text-sm text-green-700 font-medium">
                Pay once, get your translation. No hidden fees, no subscriptions, no surprises.
              </p>
            </div>
            
            {/* Pricing Tiers */}
            <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-6 mb-12">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-2xl p-4 text-center hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200">
                <div className="text-3xl font-bold text-blue-600 mb-2">$0.79</div>
                <div className="text-sm font-semibold text-neutral-900 mb-1">🧾 Short Book/Novella</div>
                <div className="text-xs text-neutral-600 mb-2">0-40K words</div>
                <div className="text-xs text-blue-700 italic">"Animal Farm" (30K)</div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-300 rounded-2xl p-4 text-center hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200 relative">
                <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-green-500 text-white text-xs px-3 py-1 rounded-full font-bold">POPULAR</div>
                <div className="text-3xl font-bold text-green-600 mb-2">$0.99</div>
                <div className="text-sm font-semibold text-neutral-900 mb-1">📘 Standard Novel</div>
                <div className="text-xs text-neutral-600 mb-2">40K-100K words</div>
                <div className="text-xs text-green-700 italic">"The Great Gatsby" (47K)</div>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-2xl p-4 text-center hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200">
                <div className="text-3xl font-bold text-purple-600 mb-2">$1.29</div>
                <div className="text-sm font-semibold text-neutral-900 mb-1">📕 Long Novel</div>
                <div className="text-xs text-neutral-600 mb-2">100K-180K words</div>
                <div className="text-xs text-purple-700 italic">"Pride and Prejudice" (122K)</div>
              </div>
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200 rounded-2xl p-4 text-center hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200">
                <div className="text-3xl font-bold text-orange-600 mb-2">$1.99</div>
                <div className="text-sm font-semibold text-neutral-900 mb-1">🏛️ Epic Novel</div>
                <div className="text-xs text-neutral-600 mb-2">180K-300K words</div>
                <div className="text-xs text-orange-700 italic">"The Stand" (240K)</div>
              </div>
              <div className="bg-gradient-to-br from-red-50 to-red-100 border border-red-200 rounded-2xl p-4 text-center hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200">
                <div className="text-3xl font-bold text-red-600 mb-2">$2.49</div>
                <div className="text-sm font-semibold text-neutral-900 mb-1">📚 Grand Epic</div>
                <div className="text-xs text-neutral-600 mb-2">300K-750K words</div>
                <div className="text-xs text-red-700 italic">"War and Peace" (587K)</div>
              </div>
            </div>

            {/* Book Category Examples */}
            <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 border-2 border-purple-200 rounded-2xl p-8 mb-8">
              <div className="text-center mb-8">
                <h4 className="font-bold text-neutral-900 text-2xl mb-2">
                  📚 Know Your Book Size
                </h4>
                <p className="text-sm text-neutral-600 max-w-2xl mx-auto">
                  See where famous classics fit in our pricing tiers
                </p>
              </div>

              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-6xl mx-auto">
                {/* Short Book/Novella */}
                <div className="bg-gradient-to-br from-blue-50 to-white rounded-xl p-5 border-2 border-blue-200 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
                  <div className="text-4xl mb-3 text-center">🧾</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2">Short Book</h5>
                  <div className="text-xs text-center text-neutral-600 mb-3">0–40K words</div>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">Animal Farm</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">Of Mice & Men</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">Metamorphosis</span>
                  </div>
                </div>

                {/* Standard Novel */}
                <div className="bg-gradient-to-br from-green-50 to-white rounded-xl p-5 border-2 border-green-300 hover:shadow-lg transition-all duration-200 hover:-translate-y-1 relative">
                  <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-green-500 text-white text-xs px-3 py-1 rounded-full font-bold">MOST POPULAR</div>
                  <div className="text-4xl mb-3 text-center">📘</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2">Standard Novel</h5>
                  <div className="text-xs text-center text-neutral-600 mb-3">40K–100K words</div>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Great Gatsby</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Fahrenheit 451</span>
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">Jane Eyre</span>
                  </div>
                </div>

                {/* Long Novel */}
                <div className="bg-gradient-to-br from-purple-50 to-white rounded-xl p-5 border-2 border-purple-200 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
                  <div className="text-4xl mb-3 text-center">📕</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2">Long Novel</h5>
                  <div className="text-xs text-center text-neutral-600 mb-3">100K–180K words</div>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">Pride & Prejudice</span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">Dune</span>
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">The Hobbit</span>
                  </div>
                </div>

                {/* Epic Novel */}
                <div className="bg-gradient-to-br from-orange-50 to-white rounded-xl p-5 border-2 border-orange-200 hover:shadow-lg transition-all duration-200 hover:-translate-y-1 md:col-span-2 lg:col-span-1">
                  <div className="text-4xl mb-3 text-center">🏛️</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2">Epic Novel</h5>
                  <div className="text-xs text-center text-neutral-600 mb-3">180K–300K words</div>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">The Stand</span>
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">Game of Thrones</span>
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">Les Misérables</span>
                  </div>
                </div>

                {/* Grand Epic */}
                <div className="bg-gradient-to-br from-red-50 to-white rounded-xl p-5 border-2 border-red-200 hover:shadow-lg transition-all duration-200 hover:-translate-y-1 md:col-span-2">
                  <div className="text-4xl mb-3 text-center">📚</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2">Grand Epic</h5>
                  <div className="text-xs text-center text-neutral-600 mb-3">300K–750K words</div>
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">War and Peace</span>
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">Atlas Shrugged</span>
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium">Count of Monte Cristo</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Real Price Comparison */}
            <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-2 border-green-300 rounded-xl p-6 mb-8">
              <div className="text-center mb-6">
                <div className="inline-flex items-center px-3 py-1 bg-green-600 text-white rounded-full text-sm font-bold mb-3">
                  📊 Real Price Comparison
                </div>
                <h4 className="font-bold text-neutral-900 text-lg mb-2">
                  How We Compare to Leading Competitors
                </h4>
                <p className="text-sm text-neutral-600">
                  Actual pricing from translateabook.com (checked Nov 2025)
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                {/* Example 1: Standard Novel */}
                <div className="bg-white rounded-xl p-5 shadow-sm border border-green-200">
                  <div className="text-center mb-4">
                    <div className="text-sm font-semibold text-neutral-700 mb-1">~55,000 Word Novel</div>
                    <div className="text-xs text-neutral-500">Most popular fiction books</div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-2 bg-green-100 rounded-lg border-2 border-green-500">
                      <span className="text-sm font-bold text-green-800">Our Price:</span>
                      <span className="text-xl font-bold text-green-600">$0.99</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between items-center p-2 bg-neutral-50 rounded">
                        <span className="text-neutral-600">Competitor Standard:</span>
                        <div className="text-right">
                          <div className="font-semibold text-neutral-800">$4.06</div>
                          <div className="text-red-600">4.1x more</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-neutral-50 rounded">
                        <span className="text-neutral-600">Competitor Pro:</span>
                        <div className="text-right">
                          <div className="font-semibold text-neutral-800">$11.09</div>
                          <div className="text-red-600">11.2x more</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Example 2: Long Novel */}
                <div className="bg-white rounded-xl p-5 shadow-sm border border-green-200">
                  <div className="text-center mb-4">
                    <div className="text-sm font-semibold text-neutral-700 mb-1">~150,000 Word Novel</div>
                    <div className="text-xs text-neutral-500">Fantasy/historical novels</div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-2 bg-green-100 rounded-lg border-2 border-green-500">
                      <span className="text-sm font-bold text-green-800">Our Price:</span>
                      <span className="text-xl font-bold text-green-600">$1.29</span>
                    </div>
                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between items-center p-2 bg-neutral-50 rounded">
                        <span className="text-neutral-600">Competitor Standard:</span>
                        <div className="text-right">
                          <div className="font-semibold text-neutral-800">$11.20</div>
                          <div className="text-red-600">8.7x more</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-2 bg-neutral-50 rounded">
                        <span className="text-neutral-600">Competitor Pro:</span>
                        <div className="text-right">
                          <div className="font-semibold text-neutral-800">$30.50</div>
                          <div className="text-red-600">23.6x more</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center mt-6">
                <p className="text-sm font-semibold text-green-800">
                  Same quality AI translation. Professional output. 5-30x cheaper.
                </p>
                <p className="text-xs text-neutral-600 mt-1">
                  We believe in fair pricing - not gouging readers and authors.
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-xl p-6 mb-8">
              <div className="text-center">
                <h4 className="font-bold text-neutral-900 mb-2 flex items-center justify-center space-x-2">
                  <span>💡</span>
                  <span>Why Our Prices Are Unbeatable</span>
                </h4>
                <p className="text-sm text-neutral-700 mb-3">
                  Built by polyglots who've paid overpriced translation services for years. We know what fair pricing looks like.
                </p>
                <div className="grid md:grid-cols-3 gap-4 text-xs">
                  <div className="bg-white/70 rounded-lg p-3">
                    <div className="font-semibold text-green-700">🚫 No Agency Markup</div>
                    <div className="text-neutral-600">Direct AI translation</div>
                  </div>
                  <div className="bg-white/70 rounded-lg p-3">
                    <div className="font-semibold text-blue-700">⚡ Automated Process</div>
                    <div className="text-neutral-600">Lower overhead costs</div>
                  </div>
                  <div className="bg-white/70 rounded-lg p-3">
                    <div className="font-semibold text-purple-700">❤️ Fair Philosophy</div>
                    <div className="text-neutral-600">Reasonable profit margins</div>
                  </div>
                </div>
              </div>
            </div>

            {/* File Requirements */}
            <div className="bg-gradient-to-r from-neutral-50 to-neutral-100 rounded-xl p-6 mb-8 border border-neutral-200">
              <h4 className="font-semibold text-neutral-900 mb-4 text-center">File Requirements</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="text-center p-3 bg-white rounded-lg">
                  <div className="text-lg font-bold text-primary-600">50MB</div>
                  <div className="text-neutral-600">Max file size</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg">
                  <div className="text-lg font-bold text-green-600">750K</div>
                  <div className="text-neutral-600">Max words</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg">
                  <div className="text-lg font-bold text-purple-600">EPUB</div>
                  <div className="text-neutral-600">Format only</div>
                </div>
              </div>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8 text-left max-w-4xl mx-auto">
              <div className="space-y-4">
                <h4 className="text-lg font-semibold text-neutral-900 flex items-center space-x-2">
                  <span>✨</span>
                  <span>What polyglots get:</span>
                </h4>
                <ul className="space-y-3 text-neutral-600">
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <span>Professional AI translation tuned by language experts</span>
                  </li>
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <span>EPUB, PDF & TXT formats for all your devices</span>
                  </li>
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <span>Preserved formatting, styling & images</span>
                  </li>
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <span>Secure delivery to your inbox</span>
                  </li>
                  <li className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <span>Privacy-first: auto-delete after 7 days</span>
                  </li>
                </ul>
              </div>
              
              <div className="space-y-4">
                <h4 className="text-lg font-semibold text-neutral-900 flex items-center space-x-2">
                  <span>🌍</span>
                  <span>50+ languages supported:</span>
                </h4>
                <p className="text-neutral-600 leading-relaxed">
                  Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Swedish, and 40+ more languages with native-level accuracy.
                </p>
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mt-4">
                  <div className="text-sm font-semibold text-neutral-900 mb-2">🗣️ Built by Language Lovers</div>
                  <div className="text-xs text-neutral-600 leading-relaxed">
                    Our team speaks 12+ languages combined. We understand the nuances that matter and have fine-tuned our AI accordingly.
                  </div>
                </div>
                <div className="space-y-3 pt-2">
                  <div className="flex items-center space-x-3 text-sm text-neutral-600">
                    <div className="p-1 bg-green-100 rounded-lg">
                      <Shield className="w-4 h-4 text-green-600" />
                    </div>
                    <span>Zero data collection - built for privacy</span>
                  </div>
                  <div className="flex items-center space-x-3 text-sm text-neutral-600">
                    <div className="p-1 bg-primary-100 rounded-lg">
                      <Zap className="w-4 h-4 text-primary-600" />
                    </div>
                    <span>Optimized for speed: 5-15 minutes average</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-sm border-t border-neutral-200 mt-24">
        <div className="max-w-4xl mx-auto px-4 py-8 text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-purple-500 rounded-xl shadow-sm">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-semibold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">EPUB Translator</div>
              <div className="text-sm text-neutral-600">Made by polyglots, for polyglots</div>
            </div>
          </div>
          <p className="text-sm text-neutral-600">© 2024 EPUB Translator</p>
          <p className="text-xs text-neutral-500 mt-1">Files automatically deleted after 7 days for your privacy</p>
        </div>
      </footer>
    </div>
  );
}