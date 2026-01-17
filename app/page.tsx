'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders, getSessionId } from '@/lib/session';
import { motion } from 'framer-motion';
import LoginPage from '@/components/LoginPage';
import MainPage from '@/components/MainPage';

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 세션 확인
    const checkAuth = async () => {
      // localStorage에 세션 ID가 없으면 바로 로그인 페이지로
      const sessionId = getSessionId();
      if (!sessionId) {
        console.log('세션 ID가 없습니다. 로그인이 필요합니다.');
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5초 타임아웃

      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/auth/check`, {
          credentials: 'include',
          headers: getAuthHeaders(),
          signal: controller.signal,
        });
        if (response.ok) {
          setIsAuthenticated(true);
        } else if (response.status === 401) {
          // 세션이 만료되었거나 인증 실패
          console.warn('세션이 만료되었습니다. 다시 로그인해주세요.');
          setIsAuthenticated(false);
          // localStorage에서 session_id 제거
          if (typeof window !== 'undefined') {
            localStorage.removeItem('session_id');
          }
        }
      } catch (error: any) {
        // 네트워크 에러는 조용히 처리 (백엔드가 실행되지 않았을 수 있음)
        if (error.name === 'AbortError' || error.name === 'TypeError' || error.message?.includes('Failed to fetch')) {
          // 백엔드 서버가 실행되지 않았거나 연결할 수 없음
          // 로그인 페이지를 표시하도록 함
          console.warn('백엔드 서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.');
        } else {
          console.error('Auth check failed:', error);
        }
      } finally {
        clearTimeout(timeoutId);
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">로딩 중...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      {!isAuthenticated ? (
        <LoginPage onLoginSuccess={() => setIsAuthenticated(true)} />
      ) : (
        <MainPage onLogout={() => setIsAuthenticated(false)} />
      )}
    </main>
  );
}
