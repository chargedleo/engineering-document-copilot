import { ApiResponse } from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public errors?: string[]
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const data: ApiResponse<T> = await response.json().catch(() => ({
    success: false,
    message: 'Invalid JSON response from server',
    data: null as unknown as T,
  }));

  if (!response.ok || !data.success) {
    throw new ApiError(
      response.status,
      data.message || `Request failed with status ${response.status}`,
      data.errors
    );
  }

  return data.data;
}

export function isBackendUnavailable(error: unknown): boolean {
  if (!error) return false;
  if (error instanceof ApiError && (error.status === 404 || error.status === 502 || error.status === 503 || error.status === 504)) {
    return true;
  }
  const msg = (typeof error === 'string' ? error : (error as Error).message || String(error)).toLowerCase();
  return (
    msg.includes('failed to fetch') ||
    msg.includes('network error') ||
    msg.includes('fetch failed') ||
    msg.includes('load failed') ||
    msg.includes('status 404') ||
    msg.includes('status 502') ||
    msg.includes('status 503') ||
    msg.includes('status 504') ||
    msg.includes('connection refused')
  );
}
