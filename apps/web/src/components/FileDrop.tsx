'use client';

import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle } from 'lucide-react';

interface FileDropProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
  maxSizeMB?: number;
}

export default function FileDrop({ onFileSelected, disabled = false, maxSizeMB = 50 }: FileDropProps) {
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
      const fileSizeMB = (file.size / 1024 / 1024).toFixed(1);
      alert(`File size limit exceeded: ${fileSizeMB}MB > ${maxSizeMB}MB maximum. Please use a smaller file.`);
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
            border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 bg-white/60 backdrop-blur-sm
            ${isDragOver ? 'border-primary-500 bg-gradient-to-br from-primary-50 to-blue-50 shadow-lg scale-105' : 'border-neutral-300 shadow-sm'}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary-400 hover:shadow-md cursor-pointer hover:-translate-y-1'}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && document.getElementById('file-input')?.click()}
        >
          <div className={`w-16 h-16 mx-auto mb-4 rounded-xl flex items-center justify-center transition-all duration-300 ${
            isDragOver ? 'bg-primary-500 shadow-lg scale-110' : 'bg-gradient-to-br from-primary-100 to-blue-100'
          }`}>
            <Upload className={`w-8 h-8 transition-all duration-300 ${
              isDragOver ? 'text-white' : 'text-primary-600'
            }`} />
          </div>
          
          <div className="space-y-2">
            <p className="text-lg font-medium text-neutral-900">
              <span className="hidden sm:inline">Drop your EPUB file here</span>
              <span className="sm:hidden">Choose EPUB file</span>
            </p>
            <p className="text-sm text-neutral-500">
              <span className="hidden sm:inline">or click to browse</span>
              <span className="sm:hidden">Tap to select from your device</span>
            </p>
            <div className="text-xs text-neutral-400 space-y-1">
              <div>Maximum file size: {maxSizeMB}MB</div>
              <div>Maximum content: 750,000 words</div>
              <div>EPUB format only</div>
            </div>
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
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-500 rounded-lg shadow-sm">
                <CheckCircle className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="font-medium text-neutral-900">{selectedFile.name}</p>
                <p className="text-sm text-neutral-600">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)} MB • Ready for translation
                </p>
              </div>
            </div>
            {!disabled && (
              <button
                onClick={clearFile}
                className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-white/50 rounded-lg transition-all duration-200"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}