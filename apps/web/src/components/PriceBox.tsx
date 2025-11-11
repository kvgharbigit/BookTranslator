'use client';

import { useState } from 'react';
import { CreditCard, Loader2, Sparkles, CheckCircle2 } from 'lucide-react';
import { LANGUAGES } from '@/lib/languages';

interface PriceBoxProps {
  tokensEst: number;
  priceCents: number;
  onPayment: (email: string, targetLang: string) => Promise<void>;
  onSkipPayment?: (email: string, targetLang: string) => Promise<void>;
  onPreview?: (targetLang: string, targetLangName: string) => void;
  disabled?: boolean;
  targetLang?: string;
  onLanguageChange?: (langCode: string) => void;
  outputFormat?: string;
  onFormatChange?: (format: string) => void;
}

export default function PriceBox({
  tokensEst,
  priceCents,
  onPayment,
  onSkipPayment,
  onPreview,
  disabled = false,
  targetLang: externalTargetLang,
  onLanguageChange,
  outputFormat: externalOutputFormat,
  onFormatChange
}: PriceBoxProps) {
  const [email, setEmail] = useState('');
  const [internalTargetLang, setInternalTargetLang] = useState('es');
  const [internalOutputFormat, setInternalOutputFormat] = useState('translation');
  const [hasRights, setHasRights] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Use external values if provided, otherwise use internal state
  const targetLang = externalTargetLang !== undefined ? externalTargetLang : internalTargetLang;
  const outputFormat = externalOutputFormat !== undefined ? externalOutputFormat : internalOutputFormat;

  const handlePayment = async () => {
    if (!hasRights) {
      alert('Please confirm you have the right to translate this file.');
      return;
    }

    if (!targetLang) {
      alert('Please select a target language.');
      return;
    }

    setIsProcessing(true);
    try {
      await onPayment(email, targetLang);
    } catch (error) {
      console.error('Payment failed:', error);
      alert('Payment failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSkipPayment = async () => {
    if (!hasRights) {
      alert('Please confirm you have the right to translate this file.');
      return;
    }

    if (!targetLang) {
      alert('Please select a target language.');
      return;
    }

    if (!onSkipPayment) return;

    setIsProcessing(true);
    try {
      await onSkipPayment(email, targetLang);
    } catch (error) {
      console.error('Skip payment failed:', error);
      alert('Failed to start translation. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handlePreview = () => {
    if (!targetLang) {
      alert('Please select a target language.');
      return;
    }

    const langName = LANGUAGES.find(lang => lang.code === targetLang)?.name || targetLang;
    if (onPreview) {
      onPreview(targetLang, langName);
    }
  };

  const priceUSD = priceCents / 100;
  const wordsEst = Math.round(tokensEst * 0.75); // More accurate word estimation
  
  // Determine book category based on token count (matching backend pricing logic)
  // Using 1 token = 0.75 words conversion
  const getBookCategory = (tokens: number) => {
    if (tokens < 53333) {
      return {
        name: 'Short Book/Novella',
        color: 'blue',
        example: '"Animal Farm"',
        range: 'Up to 40K words'
      };
    } else if (tokens < 160000) {
      return {
        name: 'Standard Novel',
        color: 'green',
        example: '"The Great Gatsby"',
        range: '40K - 120K words'
      };
    } else if (tokens < 266667) {
      return {
        name: 'Long Novel',
        color: 'purple',
        example: '"Pride and Prejudice"',
        range: '120K - 200K words'
      };
    } else if (tokens < 466667) {
      return {
        name: 'Epic Novel',
        color: 'orange',
        example: '"Game of Thrones"',
        range: '200K - 350K words'
      };
    } else {
      return {
        name: 'Grand Epic',
        color: 'red',
        example: '"War and Peace"',
        range: '350K - 750K words'
      };
    }
  };

  const bookCategory = getBookCategory(tokensEst);
  
  // Calculate PayPal fees (only payment provider)
  const paypalFee = Math.round(priceCents * 0.05 + 5);
  const optimalProvider = 'PayPal';

  return (
    <div className="w-full bg-white/80 backdrop-blur-sm border border-neutral-200 rounded-xl p-6 shadow-md">
      <div className="text-center mb-8">
        <h3 className="text-xl font-bold text-neutral-900 mb-4">
          Translation Estimate
        </h3>
        <div className="bg-gradient-to-br from-neutral-50 to-white rounded-2xl p-8 mb-6 border-2 border-neutral-200">
          <div className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold mb-4 bg-gradient-to-r from-primary-600 to-purple-600 text-white shadow-sm">
            <span className="mr-1.5">📚</span>
            <span>{bookCategory.name}</span>
          </div>
          <p className="text-lg font-bold text-neutral-800 mb-3 flex items-center justify-center space-x-2">
            <Sparkles className="w-5 h-5 text-primary-600" />
            <span>~{wordsEst.toLocaleString()} words detected</span>
          </p>
          <p className="text-5xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent mb-2">
            ${priceUSD.toFixed(2)}
          </p>
          <p className="text-base text-neutral-600 mb-2">{bookCategory.range}</p>
          <p className="text-sm text-neutral-500 italic mb-4">Similar to {bookCategory.example}</p>
          <div className="mb-4">
            <p className="text-xs font-semibold text-neutral-600 mb-2 text-center">You'll receive:</p>
            {outputFormat === 'both' ? (
              <div className="space-y-2">
                <div className="flex items-center justify-center space-x-4 text-sm font-medium text-neutral-700">
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span>EPUB</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span>PDF</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span>TXT</span>
                  </div>
                </div>
                <div className="flex items-center justify-center space-x-4 text-sm font-medium text-purple-700">
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-purple-600" />
                    <span>Bilingual EPUB</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-purple-600" />
                    <span>PDF</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-purple-600" />
                    <span>TXT</span>
                  </div>
                </div>
              </div>
            ) : outputFormat === 'bilingual' ? (
              <div className="flex items-center justify-center space-x-6 text-sm font-medium text-purple-700">
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-purple-600" />
                  <span>Bilingual EPUB</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-purple-600" />
                  <span>PDF</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-purple-600" />
                  <span>TXT</span>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center space-x-6 text-sm font-medium text-neutral-700">
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span>EPUB</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span>PDF</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  <span>TXT</span>
                </div>
              </div>
            )}
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
            <p className="text-sm font-bold text-green-800 mb-1">
              Save up to 70% vs competitors
            </p>
            <p className="text-xs text-green-700">
              Same quality, fraction of the price
            </p>
          </div>
          <div className="text-sm text-neutral-600 bg-white/80 rounded-lg p-3 border border-neutral-200">
            <div className="flex justify-between items-center mb-1">
              <span>Translation:</span>
              <span className="font-semibold">${priceUSD.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center text-xs text-neutral-500">
              <span>{optimalProvider} fee:</span>
              <span>${(paypalFee / 100).toFixed(2)}</span>
            </div>
            <div className="border-t border-neutral-200 mt-2 pt-2 flex justify-between items-center font-bold">
              <span>Total:</span>
              <span className="text-primary-600">${((priceCents + paypalFee) / 100).toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-5">
        {/* Output Format Selection */}
        <div>
          <label htmlFor="output-format" className="block text-base font-semibold text-neutral-800 mb-2">
            Output Format:
          </label>
          <select
            id="output-format"
            value={outputFormat}
            onChange={(e) => {
              const newFormat = e.target.value;
              if (onFormatChange) {
                onFormatChange(newFormat);
              } else {
                setInternalOutputFormat(newFormat);
              }
            }}
            disabled={disabled || isProcessing}
            className="w-full px-4 py-3 border-2 border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50 text-base"
          >
            <option value="translation">Translation Only - ${priceUSD.toFixed(2)}</option>
            <option value="bilingual">Bilingual Reader Only - ${(priceUSD + 1.00).toFixed(2)} (+$1.00)</option>
            <option value="both">Both Formats - ${(priceUSD + 1.50).toFixed(2)} (+$1.50)</option>
          </select>
          <p className="text-sm text-neutral-600 mt-1.5">
            {outputFormat === 'bilingual' && 'Side-by-side original + translation for learning'}
            {outputFormat === 'both' && 'Get both standard translation + bilingual reader'}
            {outputFormat === 'translation' && 'Standard translation in target language only'}
          </p>
        </div>

        {/* Target Language Selection */}
        <div>
          <label htmlFor="target-lang" className="block text-base font-semibold text-neutral-800 mb-2">
            Translate to:
          </label>
          <select
            id="target-lang"
            value={targetLang}
            onChange={(e) => {
              const newLang = e.target.value;
              if (onLanguageChange) {
                onLanguageChange(newLang);
              } else {
                setInternalTargetLang(newLang);
              }
            }}
            disabled={disabled || isProcessing}
            className="w-full px-4 py-3 border-2 border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50 text-base"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.flag} {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Email Input */}
        <div>
          <label htmlFor="email" className="block text-base font-semibold text-neutral-800 mb-2">
            Email for download link:
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your.email@example.com"
            disabled={disabled || isProcessing}
            className="w-full px-4 py-3 border-2 border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50 text-base"
          />
          <p className="text-sm text-neutral-600 mt-1.5">
            Optional but recommended
          </p>
        </div>

        {/* Preview Button */}
        {onPreview && (
          <button
            onClick={handlePreview}
            disabled={disabled || isProcessing || !targetLang}
            className="w-full bg-gradient-to-r from-blue-500 to-indigo-500 text-white py-3 px-4 rounded-xl font-medium hover:from-blue-600 hover:to-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
          >
            <Sparkles className="w-5 h-5" />
            <span>Preview Translation (Free)</span>
          </button>
        )}

        {/* Rights Confirmation */}
        <div className="bg-amber-50 border-2 border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <input
              id="rights-check"
              type="checkbox"
              checked={hasRights}
              onChange={(e) => setHasRights(e.target.checked)}
              disabled={disabled || isProcessing}
              className="mt-0.5 h-5 w-5 text-primary-600 border-2 border-neutral-400 rounded focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            />
            <label htmlFor="rights-check" className="text-base font-semibold text-neutral-900 cursor-pointer">
              I own the rights to translate this file
              <span className="block text-sm font-normal text-neutral-600 mt-1">Required to proceed</span>
            </label>
          </div>
        </div>

        {/* Payment Button */}
        <button
          onClick={handlePayment}
          disabled={disabled || isProcessing || !hasRights || !targetLang}
          className="w-full bg-gradient-to-r from-primary-600 to-purple-600 text-white py-3 px-4 rounded-xl font-medium hover:from-primary-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <CreditCard className="w-5 h-5" />
          )}
          <span>
            {isProcessing ? 'Processing...' : 'Pay & Translate'}
          </span>
        </button>

        {/* Skip Payment Button (for testing) - Only show in development */}
        {onSkipPayment && process.env.NODE_ENV === 'development' && (
          <button
            onClick={handleSkipPayment}
            disabled={disabled || isProcessing || !hasRights || !targetLang}
            className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 text-white py-3 px-4 rounded-xl font-medium hover:from-yellow-600 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center space-x-2 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
          >
            {isProcessing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Sparkles className="w-5 h-5" />
            )}
            <span>
              {isProcessing ? 'Processing...' : 'Skip Payment (Test)'}
            </span>
          </button>
        )}

        <div className="text-center">
          <p className="text-xs text-neutral-500">
            Files auto-delete after 7 days • Powered by PayPal
          </p>
        </div>
      </div>
    </div>
  );
}