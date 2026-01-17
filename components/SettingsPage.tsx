'use client';

import { useState, useEffect } from 'react';
import { getAuthHeaders } from '@/lib/session';
import { motion } from 'framer-motion';
import { Save, Key, CheckCircle2 } from 'lucide-react';
import * as Label from '@radix-ui/react-label';

interface SettingsPageProps {
  onBack: () => void;
}

export default function SettingsPage({ onBack }: SettingsPageProps) {
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    groq: '',
    gemini: '',
  });
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/settings/api-keys`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify(apiKeys),
      });

      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      } else {
        const data = await response.json();
        alert(data.detail || 'API 키 저장에 실패했습니다.');
      }
    } catch (error) {
      console.error('Save API keys error:', error);
      alert('서버에 연결할 수 없습니다.');
    }
  };

  useEffect(() => {
    // 백엔드에서 사용자별 API 키 조회
    const fetchApiKeys = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/settings/api-keys`, {
          headers: getAuthHeaders(), // X-Session-ID 헤더 추가
          credentials: 'include',
        });

        if (response.ok) {
          const data = await response.json();
          setApiKeys({
            openai: data.api_keys?.openai || '',
            groq: data.api_keys?.groq || '',
            gemini: data.api_keys?.gemini || '',
          });
        } else {
          console.error('API 키 조회 실패:', response.status, response.statusText);
        }
      } catch (error) {
        console.error('Fetch API keys error:', error);
        // 실패해도 계속 진행 (기본값 사용)
      }
    };

    fetchApiKeys();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <button
            onClick={onBack}
            className="text-gray-400 hover:text-white mb-4"
          >
            ← 뒤로가기
          </button>
          <h1 className="text-3xl font-bold mb-2">API 키 설정</h1>
          <p className="text-gray-400">각 AI 모델의 API 키를 입력하세요.</p>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 space-y-6">
          {/* OpenAI */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label.Root htmlFor="openai" className="text-sm font-medium text-gray-300 flex items-center gap-2">
                <Key className="w-4 h-4" />
                OpenAI GPT-5 Nano
              </Label.Root>
              <a
                href="https://platform.openai.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-400 hover:text-blue-300 underline"
              >
                API 키 생성하기 →
              </a>
            </div>
            <p className="text-xs text-gray-500">
              1. <a href="https://platform.openai.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">OpenAI 플랫폼</a>에 로그인<br/>
              2. API Keys 메뉴에서 "Create new secret key" 클릭<br/>
              3. 생성된 키를 복사하여 아래에 입력
            </p>
            <input
              id="openai"
              type="password"
              value={apiKeys.openai || ''}
              onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
              placeholder="sk-..."
            />
          </div>

          {/* Groq */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label.Root htmlFor="groq" className="text-sm font-medium text-gray-300 flex items-center gap-2">
                <Key className="w-4 h-4" />
                Groq
              </Label.Root>
              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-400 hover:text-blue-300 underline"
              >
                API 키 생성하기 →
              </a>
            </div>
            <p className="text-xs text-gray-500">
              1. <a href="https://console.groq.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Groq Console</a>에 로그인<br/>
              2. API Keys 메뉴로 이동<br/>
              3. "Create API Key" 버튼 클릭 후 생성된 키를 복사
            </p>
            <input
              id="groq"
              type="password"
              value={apiKeys.groq || ''}
              onChange={(e) => setApiKeys({ ...apiKeys, groq: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
              placeholder="gsk_..."
            />
          </div>

          {/* Gemini */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label.Root htmlFor="gemini" className="text-sm font-medium text-gray-300 flex items-center gap-2">
                <Key className="w-4 h-4" />
                Google Gemini 2.5 Flash-Lite
              </Label.Root>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-400 hover:text-blue-300 underline"
              >
                API 키 생성하기 →
              </a>
            </div>
            <p className="text-xs text-gray-500">
              1. <a href="https://aistudio.google.com" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">Google AI Studio</a>에 로그인<br/>
              2. "Get API key" 버튼 클릭<br/>
              3. 프로젝트 선택 또는 새 프로젝트 생성 후 키 복사
            </p>
            <input
              id="gemini"
              type="password"
              value={apiKeys.gemini || ''}
              onChange={(e) => setApiKeys({ ...apiKeys, gemini: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
              placeholder="AIza..."
            />
          </div>

          <motion.button
            onClick={handleSave}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg font-semibold flex items-center justify-center gap-2"
          >
            {saved ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                저장 완료
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                저장
              </>
            )}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
