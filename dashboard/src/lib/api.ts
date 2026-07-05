export interface ApiResult<T> {
  data: T | null;
  error: string | null;
  status: number;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
  apiKey = ''
): Promise<ApiResult<T>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  if (apiKey) headers['X-API-Key'] = apiKey;

  try {
    const res = await fetch(path, { ...options, headers });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      return { data: null, error: text || `HTTP ${res.status}`, status: res.status };
    }
    const data = (await res.json()) as T;
    return { data, error: null, status: res.status };
  } catch {
    return { data: null, error: 'Network error — is the brain running?', status: 0 };
  }
}
