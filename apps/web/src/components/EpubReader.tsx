'use client';

import { useEffect, useRef, useState } from 'react';
import ePub, { Book, Rendition } from 'epubjs';
import { ChevronLeft, ChevronRight, Loader } from 'lucide-react';

interface EpubReaderProps {
  url: string;
  className?: string;
}

export default function EpubReader({ url, className = '' }: EpubReaderProps) {
  const viewerRef = useRef<HTMLDivElement>(null);
  const [book, setBook] = useState<Book | null>(null);
  const [rendition, setRendition] = useState<Rendition | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentLocation, setCurrentLocation] = useState<string>('');

  useEffect(() => {
    if (!viewerRef.current || !url) return;

    // Initialize EPUB.js
    const epubBook = ePub(url);
    setBook(epubBook);

    // Render into the container
    const renditionInstance = epubBook.renderTo(viewerRef.current, {
      width: '100%',
      height: '100%',
      spread: 'none',
      // Preserve original EPUB styling as much as possible
      allowScriptedContent: false,
      ignoreClass: '',
    });

    setRendition(renditionInstance);

    // Apply themes to preserve original styling
    renditionInstance.themes.default({
      // Minimal overrides - let the EPUB's CSS take precedence
      '::selection': {
        'background': 'rgba(59, 130, 246, 0.3)'
      }
    });

    // Display the book
    renditionInstance.display().then(() => {
      setLoading(false);
    });

    // Track location changes
    renditionInstance.on('relocated', (location: any) => {
      setCurrentLocation(location.start.cfi);
    });

    // Cleanup
    return () => {
      renditionInstance.destroy();
    };
  }, [url]);

  const goNext = () => {
    rendition?.next();
  };

  const goPrev = () => {
    rendition?.prev();
  };

  return (
    <div className={`relative ${className}`}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90 z-10">
          <Loader className="w-8 h-8 text-primary-600 animate-spin" />
        </div>
      )}

      {/* EPUB Viewer */}
      <div ref={viewerRef} className="w-full h-full" />

      {/* Navigation Controls */}
      {!loading && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center space-x-4 bg-white/90 backdrop-blur-sm px-4 py-2 rounded-full shadow-lg border border-neutral-200">
          <button
            onClick={goPrev}
            className="p-2 hover:bg-neutral-100 rounded-full transition-colors"
            title="Previous page"
          >
            <ChevronLeft className="w-5 h-5 text-neutral-700" />
          </button>
          <span className="text-sm text-neutral-600 px-2">Swipe or click arrows</span>
          <button
            onClick={goNext}
            className="p-2 hover:bg-neutral-100 rounded-full transition-colors"
            title="Next page"
          >
            <ChevronRight className="w-5 h-5 text-neutral-700" />
          </button>
        </div>
      )}
    </div>
  );
}
