'use client';

import { useState } from 'react';
import { CreditCard, Loader2, Sparkles, CheckCircle2 } from 'lucide-react';

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
    <div className="w-full max-w-md mx-auto bg-white/80 backdrop-blur-sm border border-neutral-200 rounded-xl p-6 shadow-md">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-2">
          Translation Estimate
        </h3>
        <div className="bg-gradient-to-br from-primary-50 via-blue-50 to-purple-50 rounded-xl p-6 mb-6 border border-primary-100">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium mb-3 ${
            bookCategory.color === 'blue' ? 'bg-blue-100 text-blue-700 border border-blue-200' :
            bookCategory.color === 'green' ? 'bg-green-100 text-green-700 border border-green-200' :
            bookCategory.color === 'purple' ? 'bg-purple-100 text-purple-700 border border-purple-200' :
            bookCategory.color === 'orange' ? 'bg-orange-100 text-orange-700 border border-orange-200' :
            'bg-red-100 text-red-700 border border-red-200'
          }`}>
            <span className="mr-1">📚</span>
            <span>{bookCategory.name}</span>
          </div>
          <p className="text-sm text-neutral-600 mb-2 flex items-center justify-center space-x-2">
            <Sparkles className="w-4 h-4 text-primary-500" />
            <span>~{wordsEst.toLocaleString()} words detected</span>
          </p>
          <p className="text-4xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent mb-1">
            ${priceUSD.toFixed(2)}
          </p>
          <p className="text-sm text-neutral-600 mb-3">{bookCategory.range}</p>
          <p className="text-xs text-neutral-500 italic mb-3">Similar to {bookCategory.example}</p>
          <div className="flex items-center justify-center space-x-4 text-xs text-neutral-600 mb-3">
            <div className="flex items-center space-x-1">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              <span>EPUB</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              <span>PDF</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              <span>TXT</span>
            </div>
          </div>
          <div className="inline-flex items-center px-3 py-1 bg-white/70 text-primary-700 text-xs rounded-full border border-primary-200">
            💳 Secure payment via {optimalProvider} (${(paypalFee / 100).toFixed(2)} processing fee)
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {/* Target Language Selection */}
        <div>
          <label htmlFor="target-lang" className="block text-sm font-medium text-neutral-700 mb-1">
            Translate to:
          </label>
          <select
            id="target-lang"
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
            disabled={disabled || isProcessing}
            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
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
          <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-1">
            Email for download link:
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your.email@example.com"
            disabled={disabled || isProcessing}
            className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
          />
          <p className="text-xs text-neutral-500 mt-1">
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
            className="mt-1 h-4 w-4 text-primary-600 border-neutral-300 rounded focus:ring-primary-500 disabled:opacity-50"
          />
          <label htmlFor="rights-check" className="text-sm text-neutral-700">
            I own the rights to translate this file
          </label>
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

        <div className="text-center">
          <p className="text-xs text-neutral-500">
            Files auto-delete after 7 days • Powered by PayPal
          </p>
        </div>
      </div>
    </div>
  );
}