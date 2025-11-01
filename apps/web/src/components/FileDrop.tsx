'use client';

import { useState, useCallback } from 'react';
import { Upload, File, X } from 'lucide-react';

interface FileDropProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  maxSizeMB?: number;
}

export default function FileDrop({ onFileSelected, disabled = false, maxSizeMB = 200 }: FileDropProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    const epubFile = files.find(file => file.name.toLowerCase().endsWith('.epub'));
    
    if (epubFile) {
      handleFileSelection(epubFile);
    }
  }, [disabled]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    
    const file = e.target.files?.[0];
    if (file && file.name.toLowerCase().endsWith('.epub')) {
      handleFileSelection(file);
    }
  }, [disabled]);

  const handleFileSelection = (file: File) => {
    // Validate file size
    const maxBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxBytes) {
      alert(`File too large. Maximum size: ${maxSizeMB}MB`);
      return;
    }

    setSelectedFile(file);
    onFileSelected(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className="w-full max-w-md mx-auto">
      {!selectedFile ? (
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${isDragOver ? 'border-primary-500 bg-primary-50' : 'border-gray-300'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary-400 cursor-pointer'}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && document.getElementById('file-input')?.click()}
        >
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          
          <div className="space-y-2">
            <p className="text-lg font-medium text-gray-900">
              {/* Desktop: drag and drop, Mobile: tap to select */}
              <span className="hidden sm:inline">Drop your EPUB file here</span>
              <span className="sm:hidden">Choose EPUB file</span>
            </p>
            <p className="text-sm text-gray-500">
              <span className="hidden sm:inline">or click to browse</span>
              <span className="sm:hidden">Tap to select from your device</span>
            </p>
            <p className="text-xs text-gray-400">
              Maximum file size: {maxSizeMB}MB
            </p>
          </div>

          <input
            id="file-input"
            type="file"
            accept=".epub"
            onChange={handleFileInput}
            className="hidden"
            disabled={disabled}
          />
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <File className="w-8 h-8 text-primary-500" />
              <div>
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
            </div>
            {!disabled && (
              <button
                onClick={clearFile}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                title="Remove file"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}