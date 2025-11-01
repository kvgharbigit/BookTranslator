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
};