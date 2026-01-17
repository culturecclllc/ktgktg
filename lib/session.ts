// 세션 관리 유틸리티

const SESSION_ID_KEY = 'session_id';

export const setSessionId = (sessionId: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }
};

export const getSessionId = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem(SESSION_ID_KEY);
  }
  return null;
};

export const removeSessionId = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(SESSION_ID_KEY);
  }
};

// API 요청 헤더에 session_id 추가
export const getAuthHeaders = (): HeadersInit => {
  const sessionId = getSessionId();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (sessionId) {
    headers['X-Session-ID'] = sessionId;
  }
  
  return headers;
};
