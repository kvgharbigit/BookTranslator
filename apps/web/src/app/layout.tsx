import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EPUB Translator - Translate Books to Any Language',
  description: 'Professional EPUB translation service. Upload your book and get it translated to any language in EPUB, PDF, and TXT formats. No account required.',
  keywords: 'EPUB translator, book translation, ebook translation, multilingual books',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  );
}