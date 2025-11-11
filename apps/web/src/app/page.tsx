'use client';

import { useState } from 'react';
import { BookOpen, Zap, Globe, Shield, Sparkles, ArrowRight, Download } from 'lucide-react';
import FileDrop from '@/components/FileDrop';
import PriceBox from '@/components/PriceBox';
import PreviewSection from '@/components/PreviewSection';
import { api } from '@/lib/api';
import { LANGUAGES } from '@/lib/languages';
import { getLanguageUploadMessages } from '@/lib/uploadMessages';

type Step = 'upload' | 'estimate' | 'processing';

export default function HomePage() {
  const [step, setStep] = useState<Step>('upload');
  const [uploadKey, setUploadKey] = useState<string>('');
  const [estimate, setEstimate] = useState<{ tokens_est: number; price_cents: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [previewLang, setPreviewLang] = useState<string>('es');
  const [previewLangName, setPreviewLangName] = useState<string>('Spanish');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadMessage, setUploadMessage] = useState<string>('');
  const [outputFormat, setOutputFormat] = useState<string>('translation');

  const handleFileSelected = async (file: File) => {
    setIsLoading(true);
    setError('');
    setUploadProgress(0);

    // Language-specific upload messages
    const langMessages = getLanguageUploadMessages(previewLang, previewLangName);
    const randomStartMsg = langMessages.start[Math.floor(Math.random() * langMessages.start.length)];
    setUploadMessage(randomStartMsg);

    try {
      // Step 1: Get presigned upload URL
      const { key, upload_url } = await api.presignUpload(file.name);

      // Step 2: Upload file to R2 with progress tracking
      let lastMessagePercent = 0;
      let progressMsgIndex = 0;
      await api.uploadFileWithProgress(upload_url, file, (percent, message) => {
        setUploadProgress(percent);
        // Add fun language-specific messages based on progress
        if (percent < 30 && lastMessagePercent < 30) {
          setUploadMessage(langMessages.progress[0]);
          lastMessagePercent = 30;
        } else if (percent >= 30 && percent < 60 && lastMessagePercent < 60) {
          setUploadMessage(langMessages.progress[1] || langMessages.progress[0]);
          lastMessagePercent = 60;
        } else if (percent >= 60 && percent < 100 && lastMessagePercent < 100) {
          setUploadMessage(langMessages.progress[2] || langMessages.progress[1] || langMessages.progress[0]);
          lastMessagePercent = 100;
        }
      });

      // Step 3: Get price estimate with language-specific message
      const randomAnalyzeMsg = langMessages.analyzing[Math.floor(Math.random() * langMessages.analyzing.length)];
      setUploadMessage(randomAnalyzeMsg);
      const estimateResponse = await api.getEstimate(key, previewLang, outputFormat);

      setUploadKey(key);
      setEstimate(estimateResponse);
      setStep('estimate');

    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
      setUploadMessage('');
    }
  };

  const handlePayment = async (email: string, targetLang: string) => {
    if (!estimate || !uploadKey) return;

    try {
      const { checkout_url } = await api.createCheckout(
        uploadKey,
        targetLang,
        email,
        estimate.price_cents,
        outputFormat
      );

      // Redirect to Stripe Checkout
      window.location.href = checkout_url;

    } catch (err) {
      console.error('Payment creation failed:', err);
      throw new Error('Failed to create payment session. Please try again.');
    }
  };

  const handleSkipPayment = async (email: string, targetLang: string) => {
    if (!uploadKey) return;

    try {
      const { job_id } = await api.skipPayment(
        uploadKey,
        targetLang,
        email,
        outputFormat
      );

      // Redirect to success page (same as after payment)
      window.location.href = `/success?job_id=${job_id}`;

    } catch (err) {
      console.error('Skip payment failed:', err);
      throw new Error('Failed to start translation. Please try again.');
    }
  };

  const handleFormatChange = async (newFormat: string) => {
    setOutputFormat(newFormat);

    // Re-fetch estimate with new format
    if (uploadKey) {
      try {
        const estimateResponse = await api.getEstimate(uploadKey, previewLang, newFormat);
        setEstimate(estimateResponse);
      } catch (err) {
        console.error('Failed to update estimate:', err);
      }
    }
  };

  const resetForm = () => {
    setStep('upload');
    setUploadKey('');
    setEstimate(null);
    setError('');
    setPreviewLang('es');
    setOutputFormat('translation');
    setPreviewLangName('Spanish');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-neutral-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-primary-500 to-purple-500 rounded-xl shadow-sm">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">Polytext</h1>
                <p className="text-sm text-neutral-600">Made by language lovers, for language lovers</p>
              </div>
            </div>
            <a
              href="/retrieve"
              className="flex items-center gap-2 px-4 py-2 border-2 border-primary-600 text-primary-600 rounded-lg font-medium hover:bg-primary-50 transition-all duration-200"
            >
              <Download className="w-4 h-4" />
              <span>Get Your Books</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center mb-24">
          {/* Price Badge */}
          <div className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-600 text-white rounded-full text-lg font-bold mb-8 shadow-md hover:shadow-lg transition-all transform hover:scale-105">
            <Sparkles className="w-5 h-5" />
            <span>Book Translation from $0.99</span>
          </div>

          <h2 className="text-5xl md:text-6xl font-bold text-neutral-900 mb-8 leading-tight">
            Upload. Translate.
            <span className="bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent block">Download.</span>
          </h2>
          <p className="text-xl md:text-2xl text-neutral-700 mb-10 max-w-2xl mx-auto leading-relaxed">
            Turn any book into any language in minutes. Then pay only for what you need—no account, no subscription.
          </p>

          {/* Primary CTA */}
          <div className="mb-8">
            <button
              onClick={() => {
                const uploadSection = document.getElementById('upload-section');
                if (uploadSection) {
                  const yOffset = -100; // Offset for header height
                  const y = uploadSection.getBoundingClientRect().top + window.pageYOffset + yOffset;
                  window.scrollTo({ top: y, behavior: 'smooth' });
                }
              }}
              className="group inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-full text-lg font-bold shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
            >
              <Sparkles className="w-5 h-5" />
              <span>Try It Free Now</span>
            </button>
            <p className="text-sm text-neutral-600 mt-2">300-word preview • No payment needed</p>
          </div>

          {/* Social Proof */}
          <div className="flex items-center justify-center gap-3 text-base text-neutral-700 mb-12">
            <div className="flex -space-x-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 border-2 border-white flex items-center justify-center text-white text-xs font-semibold shadow-sm">JS</div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-purple-600 border-2 border-white flex items-center justify-center text-white text-xs font-semibold shadow-sm">MK</div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-400 to-green-600 border-2 border-white flex items-center justify-center text-white text-xs font-semibold shadow-sm">AL</div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 border-2 border-white flex items-center justify-center text-white text-xs font-semibold shadow-sm">+200K</div>
            </div>
            <span className="font-semibold">Over 200,000 books translated</span>
          </div>
          <div className="flex flex-wrap justify-center gap-8 text-sm mb-4">
            <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-5 py-2.5 rounded-full shadow-sm">
              <Globe className="w-5 h-5 text-blue-500" />
              <span className="text-neutral-700 font-semibold">47 languages</span>
            </div>
            <div className="flex items-center space-x-2 bg-white/60 backdrop-blur-sm px-5 py-2.5 rounded-full shadow-sm">
              <Shield className="w-5 h-5 text-green-500" />
              <span className="text-neutral-700 font-semibold">No account required</span>
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
        <div id="upload-section" className="flex flex-col items-center space-y-8">
          {step === 'upload' && (
            <div className="w-full max-w-2xl">
              <div className="text-center mb-10">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-bold mb-4">
                  <span>Step 1</span>
                </div>
                <h3 className="text-3xl font-bold text-neutral-900 mb-4">
                  Choose Language & Upload
                </h3>
                <p className="text-lg text-neutral-600 leading-relaxed mb-3">
                  Select your target language, then upload your EPUB for an instant price estimate
                </p>
                <p className="text-base text-primary-600 font-bold">
                  Full book translation starting at $0.99 • Free 300-word preview
                </p>
              </div>

              {/* Target Language Selection */}
              <div className="mb-8 max-w-md mx-auto">
                <label htmlFor="upload-target-lang" className="block text-lg font-semibold text-neutral-800 mb-3 text-center">
                  Translate to:
                </label>
                <select
                  id="upload-target-lang"
                  value={previewLang}
                  onChange={(e) => {
                    const newLang = e.target.value;
                    setPreviewLang(newLang);
                    const langName = LANGUAGES.find(lang => lang.code === newLang)?.name || newLang;
                    setPreviewLangName(langName);
                  }}
                  disabled={isLoading}
                  className="w-full px-4 py-3 border-2 border-neutral-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50 text-base font-medium bg-white shadow-sm"
                >
                  {LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.flag} {lang.name}
                    </option>
                  ))}
                </select>
                <p className="text-sm text-neutral-500 mt-2 text-center">
                  Select your target language before uploading
                </p>
              </div>

              <FileDrop
                onFileSelected={handleFileSelected}
                disabled={isLoading}
                maxSizeMB={50}
              />
              {isLoading && (
                <div className="text-center mt-6 space-y-4">
                  <div className="inline-flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-primary-50 to-blue-50 rounded-full border border-primary-200">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary-600 border-t-transparent"></div>
                    <p className="text-primary-700 font-medium">{uploadMessage || 'Uploading and analyzing your file...'}</p>
                  </div>
                  {uploadProgress > 0 && uploadProgress < 100 && (
                    <div className="max-w-md mx-auto">
                      <div className="w-full bg-neutral-200 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-primary-500 to-blue-500 h-full transition-all duration-300 ease-out"
                          style={{ width: `${uploadProgress}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-neutral-500 mt-1">{uploadProgress}% complete</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {step === 'estimate' && estimate && (
            <div className="w-full max-w-7xl">
              <div className="text-center mb-10">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-bold mb-4">
                  <span>Step 2</span>
                </div>
                <h3 className="text-3xl font-bold text-neutral-900 mb-4">
                  Preview & Pay
                </h3>
                <p className="text-lg text-neutral-600 leading-relaxed">
                  Check out your <strong className="text-primary-600">free 300-word preview</strong> below—see the quality before you pay
                </p>
              </div>

              {/* Two-column layout: PriceBox on left (primary action), Preview on right (supporting) */}
              <div className="grid lg:grid-cols-[1fr,1.5fr] gap-8 items-start max-w-7xl mx-auto">
                {/* Price Box - Primary Action */}
                <div className="w-full order-2 lg:order-1">
                  <div className="lg:sticky lg:top-20">
                    <PriceBox
                      tokensEst={estimate.tokens_est}
                      priceCents={estimate.price_cents}
                      onPayment={handlePayment}
                      onSkipPayment={handleSkipPayment}
                      targetLang={previewLang}
                      onLanguageChange={(langCode) => {
                        setPreviewLang(langCode);
                        const lang = LANGUAGES.find(l => l.code === langCode);
                        if (lang) setPreviewLangName(lang.name);
                      }}
                      outputFormat={outputFormat}
                      onFormatChange={handleFormatChange}
                    />
                    <div className="text-center mt-4">
                      <button
                        onClick={resetForm}
                        className="text-neutral-500 text-sm underline hover:text-neutral-700"
                      >
                        Upload a different file
                      </button>
                    </div>
                  </div>
                </div>

                {/* Preview Section - Supporting Evidence */}
                <div className="w-full order-1 lg:order-2">
                  {uploadKey && (
                    <div className="bg-white/80 backdrop-blur-sm border border-neutral-200 rounded-xl shadow-md overflow-hidden">
                      <div className="bg-gradient-to-r from-primary-600 to-purple-600 px-6 py-4">
                        <h4 className="text-lg font-semibold text-white flex items-center space-x-2">
                          <Sparkles className="w-5 h-5" />
                          <span>Free 300-Word Preview</span>
                        </h4>
                        <p className="text-primary-50 text-sm mt-1">
                          Try before you buy • Translated to {previewLangName}
                        </p>
                      </div>
                      <PreviewSection
                        epubKey={uploadKey}
                        targetLang={previewLang}
                        targetLangName={previewLangName}
                        onLanguageChange={(langCode) => {
                          setPreviewLang(langCode);
                          const lang = LANGUAGES.find(l => l.code === langCode);
                          if (lang) setPreviewLangName(lang.name);
                        }}
                      />
                    </div>
                  )}
                </div>
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
            <h4 className="text-lg font-semibold text-neutral-900 mb-2">Read Anywhere</h4>
            <p className="text-sm text-neutral-600 leading-relaxed">
              Get your translated book in EPUB, PDF, and TXT—works on any device
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
            <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-neutral-900 mb-2">Results in Minutes</h4>
            <p className="text-sm text-neutral-600 leading-relaxed">
              Upload your file and get professional-quality translation instantly
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-6 text-center shadow-sm hover:shadow-md transition-all duration-200 hover:-translate-y-1">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <h4 className="text-lg font-semibold text-neutral-900 mb-2">Complete Privacy</h4>
            <p className="text-sm text-neutral-600 leading-relaxed">
              No account, no subscription, no tracking—your books stay private
            </p>
          </div>
        </div>

        {/* Pricing Info */}
        <div className="mt-20 bg-white/80 backdrop-blur-sm rounded-xl p-8 border-2 border-neutral-200 shadow-sm">
          <div className="text-center">
            <div className="text-center mb-8">
              <div className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-yellow-100 to-orange-100 text-orange-700 rounded-full text-sm font-medium mb-3">
                🏆 Best Value on the Market
              </div>
              <h3 className="text-2xl font-bold text-neutral-900 mb-4">
                The Honest Pricing You've Been Looking For
              </h3>
              <p className="text-neutral-600 mb-4 leading-relaxed">
                Created by language lovers who understand the real cost of quality translation.
              </p>
              <p className="text-sm text-green-700 font-medium">
                Pay once, get your translation. No hidden fees, no subscriptions, no surprises.
              </p>
            </div>

            {/* Pricing Tiers */}
            <div className="flex flex-wrap justify-center gap-5 mb-16">
              <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(20%-1rem)] bg-gradient-to-br from-blue-50 to-blue-100 border-2 border-blue-200 rounded-2xl p-5 text-center hover:shadow-xl transform hover:-translate-y-2 transition-all duration-200">
                <div className="text-4xl font-bold text-blue-600 mb-3">$0.99</div>
                <div className="text-base font-bold text-neutral-900 mb-2">🧾 Short Book</div>
                <div className="text-sm text-neutral-600 mb-3">0-40K words</div>
                <div className="text-sm text-blue-700 font-medium italic">"Animal Farm" (30K)</div>
              </div>
              <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(20%-1rem)] bg-gradient-to-br from-green-50 to-green-100 border-2 border-green-400 rounded-2xl p-5 text-center hover:shadow-xl transform hover:-translate-y-2 transition-all duration-200 relative ring-2 ring-green-300">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-green-600 text-white text-xs px-4 py-1.5 rounded-full font-bold shadow-md">POPULAR</div>
                <div className="text-4xl font-bold text-green-600 mb-3">$1.49</div>
                <div className="text-base font-bold text-neutral-900 mb-2">📘 Standard Novel</div>
                <div className="text-sm text-neutral-600 mb-3">40K-120K words</div>
                <div className="text-sm text-green-700 font-medium italic">"Great Gatsby" (47K)</div>
              </div>
              <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(20%-1rem)] bg-gradient-to-br from-purple-50 to-purple-100 border-2 border-purple-200 rounded-2xl p-5 text-center hover:shadow-xl transform hover:-translate-y-2 transition-all duration-200">
                <div className="text-4xl font-bold text-purple-600 mb-3">$2.19</div>
                <div className="text-base font-bold text-neutral-900 mb-2">📕 Long Novel</div>
                <div className="text-sm text-neutral-600 mb-3">120K-200K words</div>
                <div className="text-sm text-purple-700 font-medium italic">"Pride & Prejudice" (122K)</div>
              </div>
              <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(20%-1rem)] bg-gradient-to-br from-orange-50 to-orange-100 border-2 border-orange-200 rounded-2xl p-5 text-center hover:shadow-xl transform hover:-translate-y-2 transition-all duration-200">
                <div className="text-4xl font-bold text-orange-600 mb-3">$2.99</div>
                <div className="text-base font-bold text-neutral-900 mb-2">🏛️ Epic Novel</div>
                <div className="text-sm text-neutral-600 mb-3">200K-350K words</div>
                <div className="text-sm text-orange-700 font-medium italic">"The Stand" (240K)</div>
              </div>
              <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(20%-1rem)] bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-200 rounded-2xl p-5 text-center hover:shadow-xl transform hover:-translate-y-2 transition-all duration-200">
                <div className="text-4xl font-bold text-red-600 mb-3">$3.99</div>
                <div className="text-base font-bold text-neutral-900 mb-2">📚 Grand Epic</div>
                <div className="text-sm text-neutral-600 mb-3">350K-750K words</div>
                <div className="text-sm text-red-700 font-medium italic">"War & Peace" (587K)</div>
              </div>
            </div>

            {/* Book Category Examples */}
            <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 border-2 border-purple-200 rounded-2xl p-10 mb-12">
              <div className="text-center mb-10">
                <div className="text-5xl mb-3">📚</div>
                <h4 className="font-bold text-neutral-900 text-3xl mb-3">
                  Know Your Book Size
                </h4>
                <p className="text-base text-neutral-600 max-w-2xl mx-auto">
                  See where famous classics fit in our pricing tiers
                </p>
              </div>

              <div className="flex flex-wrap justify-center gap-5 max-w-6xl mx-auto">
                {/* Short Book/Novella */}
                <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(33.333%-0.83rem)] bg-gradient-to-br from-blue-50 to-white rounded-xl p-6 border-2 border-blue-200 hover:shadow-xl transition-all duration-200 hover:-translate-y-2">
                  <div className="text-5xl mb-4 text-center">🧾</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2 text-lg">Short Book</h5>
                  <div className="text-sm text-center text-neutral-600 mb-4">0–40K words</div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">Animal Farm</span>
                    <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">Of Mice & Men</span>
                    <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">Metamorphosis</span>
                  </div>
                </div>

                {/* Standard Novel */}
                <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(33.333%-0.83rem)] bg-gradient-to-br from-green-50 to-white rounded-xl p-6 border-2 border-green-400 hover:shadow-xl transition-all duration-200 hover:-translate-y-2 relative ring-2 ring-green-300">
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-green-600 text-white text-xs px-4 py-1.5 rounded-full font-bold shadow-md">MOST POPULAR</div>
                  <div className="text-5xl mb-4 text-center">📘</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2 text-lg">Standard Novel</h5>
                  <div className="text-sm text-center text-neutral-600 mb-4">40K–120K words</div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <span className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-xs font-semibold">Great Gatsby</span>
                    <span className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-xs font-semibold">Fahrenheit 451</span>
                    <span className="px-3 py-1.5 bg-green-100 text-green-800 rounded-full text-xs font-semibold">Jane Eyre</span>
                  </div>
                </div>

                {/* Long Novel */}
                <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(33.333%-0.83rem)] bg-gradient-to-br from-purple-50 to-white rounded-xl p-6 border-2 border-purple-200 hover:shadow-xl transition-all duration-200 hover:-translate-y-2">
                  <div className="text-5xl mb-4 text-center">📕</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2 text-lg">Long Novel</h5>
                  <div className="text-sm text-center text-neutral-600 mb-4">120K–200K words</div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <span className="px-3 py-1.5 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold">Pride & Prejudice</span>
                    <span className="px-3 py-1.5 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold">Dune</span>
                    <span className="px-3 py-1.5 bg-purple-100 text-purple-800 rounded-full text-xs font-semibold">The Hobbit</span>
                  </div>
                </div>

                {/* Epic Novel */}
                <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(33.333%-0.83rem)] bg-gradient-to-br from-orange-50 to-white rounded-xl p-6 border-2 border-orange-200 hover:shadow-xl transition-all duration-200 hover:-translate-y-2">
                  <div className="text-5xl mb-4 text-center">🏛️</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2 text-lg">Epic Novel</h5>
                  <div className="text-sm text-center text-neutral-600 mb-4">200K–350K words</div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <span className="px-3 py-1.5 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">The Stand</span>
                    <span className="px-3 py-1.5 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">Game of Thrones</span>
                    <span className="px-3 py-1.5 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold">Les Misérables</span>
                  </div>
                </div>

                {/* Grand Epic */}
                <div className="w-full sm:w-[calc(50%-0.625rem)] lg:w-[calc(33.333%-0.83rem)] bg-gradient-to-br from-red-50 to-white rounded-xl p-6 border-2 border-red-200 hover:shadow-xl transition-all duration-200 hover:-translate-y-2">
                  <div className="text-5xl mb-4 text-center">📚</div>
                  <h5 className="font-bold text-neutral-900 text-center mb-2 text-lg">Grand Epic</h5>
                  <div className="text-sm text-center text-neutral-600 mb-4">350K–750K words</div>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <span className="px-3 py-1.5 bg-red-100 text-red-800 rounded-full text-xs font-semibold">War and Peace</span>
                    <span className="px-3 py-1.5 bg-red-100 text-red-800 rounded-full text-xs font-semibold">Atlas Shrugged</span>
                    <span className="px-3 py-1.5 bg-red-100 text-red-800 rounded-full text-xs font-semibold">Count of Monte Cristo</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Real Price Comparison */}
            <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 border-2 border-green-400 rounded-2xl p-10 mb-12">
              <div className="text-center mb-10">
                <div className="inline-flex items-center px-5 py-2 bg-green-600 text-white rounded-full text-base font-bold mb-4 shadow-md">
                  📊 Real Price Comparison
                </div>
                <h4 className="font-bold text-neutral-900 text-3xl mb-3">
                  How We Compare to Leading Competitors
                </h4>
                <p className="text-base text-neutral-600">
                  Actual pricing from leading competitors (checked Nov 2025)
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
                {/* Example 1: Standard Novel */}
                <div className="bg-white rounded-2xl p-7 shadow-md border-2 border-green-200 hover:shadow-xl transition-all duration-200">
                  <div className="text-center mb-5">
                    <div className="text-base font-bold text-neutral-800 mb-1">~100K Word Novel</div>
                    <div className="text-sm text-neutral-500">Most popular fiction books</div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-4 bg-gradient-to-r from-green-100 to-green-50 rounded-xl border-2 border-green-500 shadow-sm">
                      <span className="text-base font-bold text-green-800">Our Price:</span>
                      <span className="text-2xl font-bold text-green-600">$1.49</span>
                    </div>
                    <div className="space-y-2.5 text-sm">
                      <div className="flex justify-between items-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-neutral-700 font-medium">BookTranslator.ai:</span>
                        <div className="text-right">
                          <div className="font-bold text-neutral-800">$5.99</div>
                          <div className="text-orange-600 font-bold text-xs">4x more</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-neutral-700 font-medium">O.Translator:</span>
                        <div className="text-right">
                          <div className="font-bold text-neutral-800">~$5.00</div>
                          <div className="text-orange-600 font-bold text-xs">3.4x more</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-neutral-700 font-medium">NovelTranslator:</span>
                        <div className="text-right">
                          <div className="font-bold text-neutral-800">~$2.99</div>
                          <div className="text-orange-600 font-bold text-xs">2x more</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Example 2: Long Novel */}
                <div className="bg-white rounded-2xl p-7 shadow-md border-2 border-green-200 hover:shadow-xl transition-all duration-200">
                  <div className="text-center mb-5">
                    <div className="text-base font-bold text-neutral-800 mb-1">~150K Word Novel</div>
                    <div className="text-sm text-neutral-500">Fantasy/historical novels</div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-4 bg-gradient-to-r from-green-100 to-green-50 rounded-xl border-2 border-green-500 shadow-sm">
                      <span className="text-base font-bold text-green-800">Our Price:</span>
                      <span className="text-2xl font-bold text-green-600">$2.19</span>
                    </div>
                    <div className="space-y-2.5 text-sm">
                      <div className="flex justify-between items-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-neutral-700 font-medium">BookTranslator.ai:</span>
                        <div className="text-right">
                          <div className="font-bold text-neutral-800">$8.99</div>
                          <div className="text-red-600 font-bold text-xs">4.1x more</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-neutral-700 font-medium">O.Translator:</span>
                        <div className="text-right">
                          <div className="font-bold text-neutral-800">~$7.50</div>
                          <div className="text-orange-600 font-bold text-xs">3.4x more</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                        <span className="text-neutral-700 font-medium">NovelTranslator:</span>
                        <div className="text-right">
                          <div className="font-bold text-neutral-800">~$4.49</div>
                          <div className="text-red-600 font-bold text-xs">2.1x more</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center mt-8">
                <p className="text-base font-bold text-green-800 mb-2">
                  Same quality AI translation. Professional output. 2-4x cheaper.
                </p>
                <p className="text-sm text-neutral-600">
                  We believe in fair pricing—not gouging readers and authors.
                </p>
              </div>
            </div>
            
            <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-2xl p-8 mb-12">
              <div className="text-center">
                <div className="text-4xl mb-3">💡</div>
                <h4 className="font-bold text-neutral-900 mb-4 text-2xl">
                  Why Our Prices Are Unbeatable
                </h4>
                <p className="text-base text-neutral-700 mb-6 max-w-2xl mx-auto">
                  Built by language lovers who've paid overpriced translation services for years. We know what fair pricing looks like.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 text-sm max-w-4xl mx-auto">
                  <div className="bg-white/80 rounded-xl p-5 shadow-sm border border-yellow-200">
                    <div className="text-2xl mb-2">🚫</div>
                    <div className="font-bold text-green-700 mb-1">No Agency Markup</div>
                    <div className="text-neutral-600">Direct AI translation</div>
                  </div>
                  <div className="bg-white/80 rounded-xl p-5 shadow-sm border border-yellow-200">
                    <div className="text-2xl mb-2">⚡</div>
                    <div className="font-bold text-blue-700 mb-1">Automated Process</div>
                    <div className="text-neutral-600">Lower overhead costs</div>
                  </div>
                  <div className="bg-white/80 rounded-xl p-5 shadow-sm border border-yellow-200">
                    <div className="text-2xl mb-2">❤️</div>
                    <div className="font-bold text-purple-700 mb-1">Fair Philosophy</div>
                    <div className="text-neutral-600">Reasonable profit margins</div>
                  </div>
                </div>
              </div>
            </div>

            {/* File Requirements */}
            <div className="bg-gradient-to-r from-neutral-50 to-neutral-100 rounded-2xl p-8 mb-12 border-2 border-neutral-200">
              <h4 className="font-bold text-neutral-900 mb-6 text-center text-2xl">File Requirements</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-base max-w-3xl mx-auto">
                <div className="text-center p-5 bg-white rounded-xl shadow-sm border border-neutral-200">
                  <div className="text-3xl font-bold text-primary-600 mb-2">50MB</div>
                  <div className="text-neutral-600 font-medium">Max file size</div>
                </div>
                <div className="text-center p-5 bg-white rounded-xl shadow-sm border border-neutral-200">
                  <div className="text-3xl font-bold text-green-600 mb-2">750K</div>
                  <div className="text-neutral-600 font-medium">Max words</div>
                </div>
                <div className="text-center p-5 bg-white rounded-xl shadow-sm border border-neutral-200">
                  <div className="text-3xl font-bold text-purple-600 mb-2">EPUB</div>
                  <div className="text-neutral-600 font-medium">Format only</div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-10 text-left max-w-5xl mx-auto">
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-7 border-2 border-neutral-200">
                <h4 className="text-xl font-bold text-neutral-900 flex items-center space-x-2 mb-5">
                  <span className="text-2xl">✨</span>
                  <span>What you get:</span>
                </h4>
                <ul className="space-y-4 text-neutral-700">
                  <li className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0">
                      <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    </div>
                    <span className="leading-relaxed">Professional AI translation tuned by language experts</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0">
                      <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    </div>
                    <span className="leading-relaxed">EPUB, PDF & TXT formats for all your devices</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0">
                      <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    </div>
                    <span className="leading-relaxed">Preserved formatting, styling & images</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0">
                      <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    </div>
                    <span className="leading-relaxed">Secure delivery to your inbox</span>
                  </li>
                  <li className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center mt-0.5 flex-shrink-0">
                      <div className="w-2 h-2 bg-primary-600 rounded-full"></div>
                    </div>
                    <span className="leading-relaxed">Privacy-first: auto-delete after 7 days</span>
                  </li>
                </ul>
              </div>

              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-7 border-2 border-neutral-200">
                <h4 className="text-xl font-bold text-neutral-900 flex items-center space-x-2 mb-5">
                  <span className="text-2xl">🌍</span>
                  <span>47 languages supported:</span>
                </h4>
                <p className="text-neutral-700 leading-relaxed mb-5">
                  English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Swedish, and 33 more languages with native-level accuracy.
                </p>
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-5 mb-5 border border-blue-200">
                  <div className="text-base font-bold text-neutral-900 mb-2 flex items-center space-x-2">
                    <span className="text-xl">🗣️</span>
                    <span>Built by Language Lovers</span>
                  </div>
                  <div className="text-sm text-neutral-600 leading-relaxed">
                    Our team speaks 12+ languages combined. We understand the nuances that matter and have fine-tuned our AI accordingly.
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 text-neutral-700">
                    <div className="p-2 bg-green-100 rounded-xl">
                      <Shield className="w-5 h-5 text-green-600" />
                    </div>
                    <span className="leading-relaxed">Zero data collection—built for privacy</span>
                  </div>
                  <div className="flex items-center space-x-3 text-neutral-700">
                    <div className="p-2 bg-primary-100 rounded-xl">
                      <Zap className="w-5 h-5 text-primary-600" />
                    </div>
                    <span className="leading-relaxed">Optimized for speed: 5-15 minutes average</span>
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
              <div className="font-semibold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">Polytext</div>
              <div className="text-sm text-neutral-600">Every book, in your language</div>
            </div>
          </div>
          <p className="text-sm text-neutral-600">© 2024 Polytext</p>
          <p className="text-xs text-neutral-500 mt-1">Files automatically deleted after 7 days for your privacy</p>
        </div>
      </footer>
    </div>
  );
}