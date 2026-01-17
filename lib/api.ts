// API Base URL 설정
export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// API 호출 헬퍼 함수
export const apiCall = async (endpoint: string, options?: RequestInit): Promise<Response> => {
  const url = `${API_BASE_URL}${endpoint}`;
  return fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
};
