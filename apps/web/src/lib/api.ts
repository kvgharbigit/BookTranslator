const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export interface PresignUploadResponse {
  key: string;
  upload_url: string;
  max_bytes: number;
}

export interface EstimateResponse {
  tokens_est: number;
  price_cents: number;
  currency: string;
}

export interface CreateCheckoutResponse {
  checkout_url: string;
}

export interface JobStatusResponse {
  id: string;
  status: string;
  progress_step: string;
  progress_percent: number;
  created_at: string;
  download_urls?: {
    epub?: string;
    pdf?: string;
    txt?: string;
  };
  expires_at?: string;
  error?: string;
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(response.status, errorData.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  // Generate presigned upload URL
  async presignUpload(filename: string): Promise<PresignUploadResponse> {
    return apiCall('/presign-upload', {
      method: 'POST',
      body: JSON.stringify({
        filename,
        content_type: 'application/epub+zip',
      }),
    });
  },

  // Upload file directly to R2
  async uploadFile(uploadUrl: string, file: File): Promise<void> {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': 'application/epub+zip',
      },
    });

    if (!response.ok) {
      throw new Error('File upload failed');
    }
  },

  // Upload file with progress tracking
  uploadFileWithProgress(
    uploadUrl: string,
    file: File,
    onProgress: (percent: number, message: string) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Fun progress messages based on upload percentage
      const getProgressMessage = (percent: number): string => {
        const messages = {
          0: '📤 Starting upload...',
          10: '🚀 Launching your book into the cloud...',
          20: '☁️ Uploading to the digital library...',
          30: '📚 Pages flying through cyberspace...',
          40: '⚡ Almost halfway there...',
          50: '🎯 Halfway point! Keep going...',
          60: '💨 Zooming through the upload...',
          70: '🌟 Making great progress...',
          80: '🔥 Nearly there...',
          90: '✨ Final stretch...',
          95: '🎊 Just a moment more...',
          100: '✅ Upload complete!',
        };

        // Find the closest message for current progress
        const thresholds = Object.keys(messages).map(Number).sort((a, b) => a - b);
        const closest = thresholds.reduce((prev, curr) =>
          Math.abs(curr - percent) < Math.abs(prev - percent) ? curr : prev
        );

        return messages[closest as keyof typeof messages];
      };

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          const message = getProgressMessage(percent);
          onProgress(percent, message);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          onProgress(100, '✅ Upload complete!');
          resolve();
        } else {
          reject(new Error('File upload failed'));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('File upload failed'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('File upload cancelled'));
      });

      xhr.open('PUT', uploadUrl);
      xhr.setRequestHeader('Content-Type', 'application/epub+zip');
      xhr.send(file);
    });
  },

  // Get price estimate
  async getEstimate(key: string, targetLang: string): Promise<EstimateResponse> {
    return apiCall('/estimate', {
      method: 'POST',
      body: JSON.stringify({
        key,
        target_lang: targetLang,
      }),
    });
  },

  // Create Stripe checkout session
  async createCheckout(
    key: string,
    targetLang: string,
    email: string,
    priceCents: number,
    provider?: string
  ): Promise<CreateCheckoutResponse> {
    return apiCall('/create-checkout', {
      method: 'POST',
      body: JSON.stringify({
        key,
        target_lang: targetLang,
        email: email || undefined,
        price_cents: priceCents,
        provider,
      }),
    });
  },

  // Skip payment and directly create job (for testing)
  async skipPayment(
    key: string,
    targetLang: string,
    email: string
  ): Promise<{ job_id: string }> {
    return apiCall('/skip-payment', {
      method: 'POST',
      body: JSON.stringify({
        key,
        target_lang: targetLang,
        email: email || undefined,
      }),
    });
  },

  // Get job status
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    return apiCall(`/job/${jobId}`);
  },

  // Generate preview translation
  async generatePreview(
    key: string,
    targetLang: string,
    maxWords: number = 1000
  ): Promise<{
    preview_html: string;
    word_count: number;
    provider: string;
    model: string;
  }> {
    return apiCall('/preview', {
      method: 'POST',
      body: JSON.stringify({
        key,
        target_lang: targetLang,
        max_words: maxWords,
      }),
    });
  },

  // Generate preview with SSE streaming (for real-time progress)
  streamPreview(
    key: string,
    targetLang: string,
    maxWords: number = 250,
    onProgress: (message: string) => void,
    onComplete: (data: {
      preview_html: string;
      word_count: number;
      provider: string;
      model: string;
    }) => void,
    onError: (error: string) => void
  ): EventSource {
    const url = `${API_BASE}/preview/stream?key=${encodeURIComponent(key)}&target_lang=${encodeURIComponent(targetLang)}&max_words=${maxWords}`;
    console.log('🔗 Connecting to SSE:', url);
    const eventSource = new EventSource(url);

    eventSource.addEventListener('progress', (event) => {
      console.log('📨 SSE progress event:', event.data);
      const data = JSON.parse(event.data);
      onProgress(data.message);
    });

    eventSource.addEventListener('complete', (event) => {
      console.log('✅ SSE complete event:', event.data);
      const data = JSON.parse(event.data);
      onComplete(data);
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      console.log('❌ SSE error event:', event);
      const data = JSON.parse((event as MessageEvent).data || '{}');
      onError(data.error || 'Preview generation failed');
      eventSource.close();
    });

    eventSource.onopen = () => {
      console.log('✅ SSE connection opened');
    };

    eventSource.onerror = (error) => {
      console.error('❌ SSE connection error:', error);
      onError('Connection lost. Please try again.');
      eventSource.close();
    };

    return eventSource;
  },
};