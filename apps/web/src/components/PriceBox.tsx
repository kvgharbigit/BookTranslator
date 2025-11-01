'use client';

import { useState } from 'react';
import { CreditCard, Loader2 } from 'lucide-react';

interface PriceBoxProps {
  tokensEst: number;
  priceCents: number;
  onPayment: (email: string, targetLang: string) => Promise<void>;
  disabled?: boolean;
}

// Language options for translation
const LANGUAGES = [
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'ru', name: 'Russian' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'nl', name: 'Dutch' },
  { code: 'sv', name: 'Swedish' },
  { code: 'da', name: 'Danish' },
  { code: 'no', name: 'Norwegian' },
  { code: 'fi', name: 'Finnish' },
  { code: 'pl', name: 'Polish' },
  { code: 'tr', name: 'Turkish' },
  { code: 'he', name: 'Hebrew' },
  { code: 'th', name: 'Thai' },
];

export default function PriceBox({ tokensEst, priceCents, onPayment, disabled = false }: PriceBoxProps) {
  const [email, setEmail] = useState('');
  const [targetLang, setTargetLang] = useState('es');
  const [hasRights, setHasRights] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

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

  const priceUSD = priceCents / 100;
  const charactersEst = tokensEst * 4; // Rough estimation

  return (
    <div className="w-full max-w-md mx-auto bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Translation Estimate
        </h3>
        <div className="space-y-1">
          <p className="text-sm text-gray-600">
            ~{charactersEst.toLocaleString()} characters
          </p>
          <p className="text-3xl font-bold text-primary-600">
            ${priceUSD.toFixed(2)} USD
          </p>
          <p className="text-xs text-gray-500">
            You'll get EPUB + PDF + TXT formats
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {/* Target Language Selection */}
        <div>
          <label htmlFor="target-lang" className="block text-sm font-medium text-gray-700 mb-1">
            Translate to:
          </label>
          <select
            id="target-lang"
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            disabled={disabled || isProcessing}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        {/* Email Input */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email for download link:
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your.email@example.com"
            disabled={disabled || isProcessing}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
          />
          <p className="text-xs text-gray-500 mt-1">
            Optional but recommended
          </p>
        </div>

        {/* Rights Confirmation */}
        <div className="flex items-start space-x-2">
          <input
            id="rights-check"
            type="checkbox"
            checked={hasRights}
            onChange={(e) => setHasRights(e.target.checked)}
            disabled={disabled || isProcessing}
            className="mt-1 h-4 w-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500 disabled:opacity-50"
          />
          <label htmlFor="rights-check" className="text-sm text-gray-700">
            I own the rights to translate this file
          </label>
        </div>

        {/* Payment Button */}
        <button
          onClick={handlePayment}
          disabled={disabled || isProcessing || !hasRights || !targetLang}
          className="w-full bg-primary-600 text-white py-3 px-4 rounded-md font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
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

        <div className="text-center">
          <p className="text-xs text-gray-500">
            Files auto-delete after 7 days • Powered by Stripe
          </p>
        </div>
      </div>
    </div>
  );
}