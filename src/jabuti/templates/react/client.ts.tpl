import { apiUrl } from './config';

export type QueryParams = Record<string, string | number | boolean | undefined>;

/** The only HTTP entry point used by Commands and Queries. */
export interface ApiClient {
  get<T>(path: string, params?: QueryParams): Promise<T>;
  post<T>(path: string, body?: unknown): Promise<T>;
  put<T>(path: string, body?: unknown): Promise<T>;
  patch<T>(path: string, body?: unknown): Promise<T>;
  delete<T>(path: string): Promise<T>;
}

/** A response outside the 2xx range. */
export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

export function createFetchApiClient(baseUrl?: string): ApiClient {
  async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    params?: QueryParams,
  ): Promise<T> {
    const response = await fetch(withParams(apiUrl(path, baseUrl), params), {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await readBody(response);
    if (!response.ok) {
      throw new ApiError(response.status, errorMessage(response, payload), payload);
    }
    return payload as T;
  }

  return {
    get: <T>(path: string, params?: QueryParams) =>
      request<T>('GET', path, undefined, params),
    post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
    put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
    patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
    delete: <T>(path: string) => request<T>('DELETE', path),
  };
}

export const apiClient: ApiClient = createFetchApiClient();

function withParams(url: string, params?: QueryParams): string {
  const search = new URLSearchParams();
  for (const [name, value] of Object.entries(params ?? {})) {
    if (value !== undefined) {
      search.append(name, String(value));
    }
  }
  const query = search.toString();
  return query ? `${url}?${query}` : url;
}

async function readBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }
  const type = response.headers.get('Content-Type') ?? '';
  return type.includes('application/json') ? response.json() : response.text();
}

function errorMessage(response: Response, payload: unknown): string {
  if (payload && typeof payload === 'object') {
    const { message, detail } = payload as { message?: unknown; detail?: unknown };
    if (typeof message === 'string') return message;
    if (typeof detail === 'string') return detail;
  }
  return `${response.status} ${response.statusText}`.trim();
}
