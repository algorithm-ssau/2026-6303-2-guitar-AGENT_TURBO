export interface AuthUser {
  id: number;
  login: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}

const API_BASE_URL = '/api/auth';

async function requestAuth(path: string, login: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ login, password }),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Ошибка сервера: ${response.status}`);
  }

  return data as AuthResponse;
}

export function login(loginValue: string, password: string): Promise<AuthResponse> {
  return requestAuth('login', loginValue, password);
}

export function register(loginValue: string, password: string): Promise<AuthResponse> {
  return requestAuth('register', loginValue, password);
}

export async function fetchMe(token: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Ошибка сервера: ${response.status}`);
  }
  return data as AuthUser;
}
