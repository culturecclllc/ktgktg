'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LogOut, Sparkles, Loader2, CheckCircle2, TrendingUp, Edit, Eye, ArrowRight, ArrowLeft, Copy, Code, Home, Menu, X, ChevronUp, ChevronDown, HelpCircle, Zap, FileText } from 'lucide-react';
import * as Label from '@radix-ui/react-label';
import * as Select from '@radix-ui/react-select';
import SettingsPage from './SettingsPage';
import HistoryPage from './HistoryPage';
import { getAuthHeaders, getSessionId } from '@/lib/session';

interface MainPageProps {
  onLogout: () => void;
}

type ArticleIntent = '정보성' | '방문후기/여행기' | '제품 리뷰/홍보' | '튜토리얼' | '비교/리뷰' | '문제 해결 가이드' | '교육/강의' | '스토리텔링' | '브랜딩' | '설득/마케팅' | '엔터테인먼트' | '맛집' | '일상생각' | '상품리뷰' | '경제비즈니스' | 'IT컴퓨터' | '교육학문';
type ToneStyle = '친절하고 명확하게' | '전문적이고 간결하게' | '대화체로 친근하게' | '유머러스하게' | '권위적으로 신뢰감 있게' | '감성적이고 따뜻하게' | '객관적이고 중립적으로' | '열정적이고 동기부여' | '비판적이고 분석적으로' | '직접 입력';
type AgeGroup = '전체' | '10대' | '20대' | '30대' | '40대' | '50대' | '60대+';
type Gender = '전체' | '남성' | '여성';

interface DraftResult {
  model: string;
  content: string;
  status: 'idle' | 'generating' | 'success' | 'error';
  error?: string;
}

interface AnalysisResult {
  model: string;
  pros: string[];
  cons: string[];
  improvement: string;
  status: 'idle' | 'analyzing' | 'success' | 'error';
  error?: string;
}

export default function MainPage({ onLogout }: MainPageProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedDraft, setSelectedDraft] = useState<{ model: string; content: string } | null>(null);
  
  // 플로팅 버튼 상태
  const [showFloatingMenu, setShowFloatingMenu] = useState(() => {
    const saved = localStorage.getItem('floating_menu_visible');
    return saved !== null ? saved === 'true' : true;
  });
  const [isFloatingMenuOpen, setIsFloatingMenuOpen] = useState(false);

  // Step 1: 주제 입력
  const [topic, setTopic] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [detailedKeywords, setDetailedKeywords] = useState('');
  const [articleIntents, setArticleIntents] = useState<ArticleIntent[]>([]);
  const [toneStyle, setToneStyle] = useState<ToneStyle>('친절하고 명확하게');
  const [customToneStyle, setCustomToneStyle] = useState('');
  const [ageGroups, setAgeGroups] = useState<AgeGroup[]>(['전체']);
  const [gender, setGender] = useState<Gender>('전체');

  // Step 2: 초안 생성
  const [drafts, setDrafts] = useState<DraftResult[]>([
    { model: 'ChatGPT', content: '', status: 'idle' },
    { model: 'Gemini', content: '', status: 'idle' },
    { model: 'Groq', content: '', status: 'idle' },
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showConfirmStep2, setShowConfirmStep2] = useState(false);

  // Step 3: 장단점 분석
  const [analyses, setAnalyses] = useState<AnalysisResult[]>([
    { model: 'ChatGPT', pros: [], cons: [], improvement: '', status: 'idle' },
    { model: 'Gemini', pros: [], cons: [], improvement: '', status: 'idle' },
    { model: 'Groq', pros: [], cons: [], improvement: '', status: 'idle' },
  ]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Step 4: 최종 생성
  const [finalContent, setFinalContent] = useState('');
  const [isGeneratingFinal, setIsGeneratingFinal] = useState(false);
  const [displayedFinalContent, setDisplayedFinalContent] = useState('');
  
  // 타이핑 애니메이션을 위한 상태
  const [displayedDraftContent, setDisplayedDraftContent] = useState<{ [key: string]: string }>({});
  const typingIntervalRef = useRef<{ [key: string]: NodeJS.Timeout }>({});
  
  // 사용자별 API 키 (백엔드에서 조회)
  const [apiKeys, setApiKeys] = useState<{ openai: string; groq: string; gemini: string }>({
    openai: '',
    groq: '',
    gemini: '',
  });
  
  // 컴포넌트 마운트 시 API 키 조회
  useEffect(() => {
    const fetchApiKeys = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/settings/api-keys`, {
          credentials: 'include',
          headers: getAuthHeaders(),
        });

        if (response.ok) {
          const data = await response.json();
          setApiKeys({
            openai: data.api_keys?.openai || '',
            groq: data.api_keys?.groq || '',
            gemini: data.api_keys?.gemini || '',
          });
        }
      } catch (error) {
        console.error('Fetch API keys error:', error);
        // 실패해도 계속 진행 (기본값 사용)
      }
    };

    fetchApiKeys();
  }, [showSettings]); // 설정 페이지를 열었다가 닫으면 다시 조회

  const toggleArticleIntent = (intent: ArticleIntent) => {
    setArticleIntents(prev => 
      prev.includes(intent) 
        ? prev.filter(i => i !== intent)
        : [...prev, intent]
    );
  };

  const toggleAgeGroup = (age: AgeGroup) => {
    if (age === '전체') {
      setAgeGroups(['전체']);
    } else {
      setAgeGroups(prev => {
        const filtered = prev.filter(a => a !== '전체');
        return filtered.includes(age) 
          ? filtered.filter(a => a !== age)
          : [...filtered, age];
      });
    }
  };

  const handleNextToStep2 = () => {
    if (!topic.trim() || !targetAudience.trim()) {
      alert('주제와 대상 독자를 입력해주세요.');
      return;
    }
    setCurrentStep(2);
    setShowConfirmStep2(true);
  };

  const handleGenerateDrafts = async () => {
    setShowConfirmStep2(false);
    setIsGenerating(true);
    
    // 초기 상태 설정 - 각 모델을 generating 상태로
    setDrafts([
      { model: 'ChatGPT', content: '', status: 'generating' },
      { model: 'Gemini', content: '', status: 'generating' },
      { model: 'Groq', content: '', status: 'generating' },
    ]);

    const models = [
      { name: 'ChatGPT', apiName: 'openai' },
      { name: 'Gemini', apiName: 'gemini' },
      { name: 'Groq', apiName: 'groq' },
    ];

    // API 키는 state에서 가져오기 (이미 useEffect에서 조회함)

    // 각 모델별로 독립적으로 처리하여 실시간 업데이트
    const promises = models.map(async (model) => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/generate/draft`, {
          method: 'POST',
          headers: getAuthHeaders(),
          credentials: 'include',
          body: JSON.stringify({
            topic,
            article_intent: articleIntents.join(', '),
            target_audience: targetAudience,
            tone_style: toneStyle === '직접 입력' ? customToneStyle : toneStyle,
            detailed_keywords: detailedKeywords,
            age_groups: ageGroups,
            gender,
            model: model.apiName,
            api_key: apiKeys[model.apiName as keyof typeof apiKeys] || '',
          }),
        });

        let data;
        try {
          data = await response.json();
        } catch {
          data = { detail: '응답을 파싱할 수 없습니다.' };
        }

        // 각 모델의 응답이 도착하는 대로 즉시 업데이트
        if (response.ok) {
          const fullContent = data.content;
          setDrafts(prev => prev.map(d => 
            d.model === model.name 
              ? { model: model.name, content: fullContent, status: 'success' as const }
              : d
          ));
          
          // 타이핑 애니메이션 시작 (ActionChains send_keys 방식: 한 글자씩 0.03초 간격)
          setDisplayedDraftContent(prev => ({ ...prev, [model.name]: '' }));
          let currentIndex = 0;
          const typingSpeed = 30; // 0.03초 = 30ms (사람이 쓰는 것처럼)
          
          typingIntervalRef.current[model.name] = setInterval(() => {
            if (currentIndex < fullContent.length) {
              setDisplayedDraftContent(prev => ({
                ...prev,
                [model.name]: fullContent.substring(0, currentIndex + 1)
              }));
              currentIndex++;
            } else {
              if (typingIntervalRef.current[model.name]) {
                clearInterval(typingIntervalRef.current[model.name]);
                delete typingIntervalRef.current[model.name];
              }
            }
          }, typingSpeed);
          
          return {
            model: model.name,
            content: fullContent,
            status: 'success' as const,
          };
        } else {
          // 에러 메시지 추출 및 개선
          let errorMessage = '생성 실패';
          let rawError = data.detail || data.error || '';
          
          // 에러 메시지 파싱 및 사용자 친화적으로 변환
          if (rawError) {
            // OpenAI 할당량 초과 에러
            if (rawError.includes('insufficient_quota') || rawError.includes('quota') || rawError.includes('할당량')) {
              errorMessage = 'OpenAI API 할당량이 초과되었습니다.\n계정의 결제 정보와 사용량을 확인해주세요.\nhttps://platform.openai.com/usage';
            }
            // Groq 모델 폐기 에러
            else if (rawError.includes('model_decommissioned') || rawError.includes('decommissioned') || rawError.includes('llama-3.1-70b-versatile')) {
              errorMessage = '사용 중인 Groq 모델이 더 이상 지원되지 않습니다.\nllama-3.3-70b-versatile 모델로 업데이트되었습니다.\nhttps://console.groq.com/docs/deprecations';
            }
            // OpenAI 요청 한도 초과
            else if (rawError.includes('rate_limit') || rawError.includes('429')) {
              errorMessage = 'API 요청 한도가 초과되었습니다.\n잠시 후 다시 시도해주세요.';
            }
            // API 키 오류
            else if (rawError.includes('invalid_api_key') || rawError.includes('authentication') || rawError.includes('API 키')) {
              errorMessage = 'API 키가 유효하지 않습니다.\n설정에서 API 키를 확인해주세요.';
            }
            // 원본 메시지에서 핵심 부분만 추출
            else {
              // "Error code: XXX - {'error': {...}}" 형식에서 메시지만 추출
              const messageMatch = rawError.match(/'message':\s*'([^']+)'/);
              if (messageMatch) {
                errorMessage = messageMatch[1];
              } else if (typeof rawError === 'string') {
                // 너무 긴 에러 메시지는 앞부분만 표시
                errorMessage = rawError.length > 200 ? rawError.substring(0, 200) + '...' : rawError;
              }
            }
          }
          
          setDrafts(prev => prev.map(d => 
            d.model === model.name 
              ? { model: model.name, content: '', status: 'error' as const, error: errorMessage }
              : d
          ));
          return {
            model: model.name,
            content: '',
            status: 'error' as const,
            error: errorMessage,
          };
        }
      } catch (error: any) {
        // 네트워크 에러 등 처리
        let errorMessage = '네트워크 오류가 발생했습니다.';
        const errorStr = error.message || String(error) || '';
        
        // 에러 메시지 파싱
        if (errorStr.includes('insufficient_quota') || errorStr.includes('quota')) {
          errorMessage = 'OpenAI API 할당량이 초과되었습니다.\n계정의 결제 정보와 사용량을 확인해주세요.';
        } else if (errorStr.includes('model_decommissioned') || errorStr.includes('llama-3.1-70b-versatile')) {
          errorMessage = '사용 중인 Groq 모델이 더 이상 지원되지 않습니다.\nllama-3.3-70b-versatile 모델로 업데이트되었습니다.';
        } else if (errorStr.includes('rate_limit') || errorStr.includes('429')) {
          errorMessage = 'API 요청 한도가 초과되었습니다.\n잠시 후 다시 시도해주세요.';
        } else if (errorStr.includes('invalid_api_key') || errorStr.includes('authentication')) {
          errorMessage = 'API 키가 유효하지 않습니다.\n설정에서 API 키를 확인해주세요.';
        } else if (errorStr) {
          errorMessage = errorStr.length > 200 ? errorStr.substring(0, 200) + '...' : errorStr;
        }
        
        setDrafts(prev => prev.map(d => 
          d.model === model.name 
            ? { model: model.name, content: '', status: 'error' as const, error: errorMessage }
            : d
        ));
        return {
          model: model.name,
          content: '',
          status: 'error' as const,
          error: errorMessage,
        };
      }
    });

    // 모든 요청 완료 대기
    await Promise.all(promises);
    setIsGenerating(false);
  };

  const handleAnalyzeDrafts = async () => {
    const hasSuccess = drafts.some(d => d.status === 'success');
    if (!hasSuccess) {
      alert('최소 1개 모델의 초안이 생성되어야 분석할 수 있습니다.');
      return;
    }
    
    // 성공한 초안만 분석 대상으로 사용
    const successfulDrafts = drafts.filter(d => d.status === 'success');
    if (successfulDrafts.length === 0) {
      alert('분석할 초안이 없습니다.');
      return;
    }

    setCurrentStep(3);
    setIsAnalyzing(true);
    
    const models = [
      { name: 'ChatGPT', apiName: 'openai' },
      { name: 'Gemini', apiName: 'gemini' },
      { name: 'Groq', apiName: 'groq' },
    ];
    
    // 성공한 초안이 있는 모델만 분석 상태로 설정
    setAnalyses(models.map(model => {
      const draft = drafts.find(d => d.model === model.name);
      return {
        model: model.name,
        pros: [],
        cons: [],
        improvement: '',
        status: (draft && draft.status === 'success') ? 'analyzing' as const : 'idle' as const,
      };
    }));

    const promises = models.map(async (model) => {
      try {
        const draft = drafts.find(d => d.model === model.name);
        if (!draft || draft.status !== 'success') {
          // 초안이 없는 경우 분석 건너뛰기
          return {
            model: model.name,
            pros: [],
            cons: [],
            improvement: '',
            status: 'idle' as const,
          };
        }

        // API 키 가져오기
        const savedApiKeys = localStorage.getItem('api_keys');
        const apiKeys = savedApiKeys ? JSON.parse(savedApiKeys) : {};

        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const response = await fetch(`${backendUrl}/api/analyze/draft`, {
          method: 'POST',
          headers: getAuthHeaders(),
          credentials: 'include',
          body: JSON.stringify({
            draft_content: draft.content,
            model: model.apiName,
            api_key: apiKeys[model.apiName as keyof typeof apiKeys] || '',
          }),
        });

        const data = await response.json();

        if (response.ok) {
          return {
            model: model.name,
            pros: data.pros || [],
            cons: data.cons || [],
            improvement: data.improvement || '',
            status: 'success' as const,
          };
        } else {
          return {
            model: model.name,
            pros: [],
            cons: [],
            improvement: '',
            status: 'error' as const,
            error: data.detail || '분석 실패',
          };
        }
      } catch (error) {
        return {
          model: model.name,
          pros: [],
          cons: [],
          improvement: '',
          status: 'error' as const,
          error: String(error),
        };
      }
    });

    // 모든 분석이 완료될 때까지 기다림
    const results = await Promise.all(promises);
    
    // 모든 결과가 완료된 후 한번에 업데이트 (짤림 방지)
    setAnalyses(results);
    setIsAnalyzing(false);
  };
  
  // 컴포넌트 언마운트 시 타이핑 애니메이션 정리
  useEffect(() => {
    return () => {
      Object.values(typingIntervalRef.current).forEach(interval => {
        if (interval) clearInterval(interval);
      });
    };
  }, []);
  
  // 모달이 열릴 때 타이핑 애니메이션 시작
  useEffect(() => {
    if (selectedDraft && !displayedDraftContent[selectedDraft.model]) {
      const fullContent = selectedDraft.content;
      setDisplayedDraftContent(prev => ({ ...prev, [selectedDraft.model]: '' }));
      let currentIndex = 0;
      const typingSpeed = 30; // 0.03초 = 30ms (ActionChains send_keys 방식)
      
      typingIntervalRef.current[`modal_${selectedDraft.model}`] = setInterval(() => {
        if (currentIndex < fullContent.length) {
          setDisplayedDraftContent(prev => ({
            ...prev,
            [selectedDraft.model]: fullContent.substring(0, currentIndex + 1)
          }));
          currentIndex++;
        } else {
          if (typingIntervalRef.current[`modal_${selectedDraft.model}`]) {
            clearInterval(typingIntervalRef.current[`modal_${selectedDraft.model}`]);
            delete typingIntervalRef.current[`modal_${selectedDraft.model}`];
          }
        }
      }, typingSpeed);
      
      return () => {
        if (typingIntervalRef.current[`modal_${selectedDraft.model}`]) {
          clearInterval(typingIntervalRef.current[`modal_${selectedDraft.model}`]);
          delete typingIntervalRef.current[`modal_${selectedDraft.model}`];
        }
      };
    }
  }, [selectedDraft]);

  const handleGenerateFinal = async () => {
    // 최소 1개 이상의 분석이 완료되어야 함
    const hasAnalyzed = analyses.some(a => a.status === 'success');
    if (!hasAnalyzed) {
      alert('최소 1개 모델의 장단점 분석이 완료되어야 합니다.');
      return;
    }

    setCurrentStep(4);
    setIsGeneratingFinal(true);
    setFinalContent('');
    setDisplayedFinalContent('');

    try {
      // API 키 가져오기 (최종 생성은 Gemini 사용)
      const savedApiKeys = localStorage.getItem('api_keys');
      const apiKeys = savedApiKeys ? JSON.parse(savedApiKeys) : {};

      // 성공한 초안과 분석만 사용
      const successfulDrafts = drafts.filter(d => d.status === 'success');
      const successfulAnalyses = analyses.filter(a => a.status === 'success');

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/generate/final`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
          topic,
          article_intent: articleIntents.join(', '),
          target_audience: targetAudience,
          tone_style: toneStyle === '직접 입력' ? customToneStyle : toneStyle,
          drafts: successfulDrafts.map(d => ({
            model: d.model,
            content: d.content,
          })),
          analyses: successfulAnalyses.map(a => ({
            model: a.model,
            pros: a.pros,
            cons: a.cons,
            improvement: a.improvement,
          })),
          api_key: apiKeys.gemini || '',
          model: 'gemini',
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const fullContent = data.content;
        setFinalContent(fullContent);
        setDisplayedFinalContent('');
        
        // 타이핑 애니메이션 시작 (ActionChains send_keys 방식: 한 글자씩 0.03초 간격)
        let currentIndex = 0;
        const typingSpeed = 30; // 0.03초 = 30ms (사람이 쓰는 것처럼)
        
        const typingInterval = setInterval(() => {
          if (currentIndex < fullContent.length) {
            setDisplayedFinalContent(fullContent.substring(0, currentIndex + 1));
            currentIndex++;
          } else {
            clearInterval(typingInterval);
          }
        }, typingSpeed);
      } else {
        alert(`최종 생성 실패: ${data.detail || '알 수 없는 오류'}`);
      }
    } catch (error) {
      alert(`서버 오류: ${error}`);
    } finally {
      setIsGeneratingFinal(false);
    }
  };

  const handleLogout = async () => {
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      await fetch(`${backendUrl}/api/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
      });
      onLogout();
    } catch (error) {
      console.error('Logout error:', error);
      onLogout();
    }
  };

  const getModelBorderColor = (model: string) => {
    switch (model) {
      case 'ChatGPT':
        return 'border-green-500';
      case 'Gemini':
        return 'border-blue-500';
      case 'Groq':
        return 'border-orange-500';
      default:
        return 'border-gray-500';
    }
  };

  const getModelIcon = (model: string) => {
    switch (model) {
      case 'ChatGPT':
        return (
          <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xs">GPT</span>
          </div>
        );
      case 'Gemini':
        return (
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xs">G</span>
          </div>
        );
      case 'Groq':
        return (
          <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xs">GQ</span>
          </div>
        );
      default:
        return null;
    }
  };

  if (showSettings) {
    return <SettingsPage onBack={() => setShowSettings(false)} />;
  }

  if (showHistory) {
    return <HistoryPage onBack={() => setShowHistory(false)} />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 헤더 */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">YNK 블로그 자동화</h1>
                <p className="text-sm text-gray-400">최고의 블로그 에이전트</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowHistory(true)}
                className="px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors flex items-center gap-2"
              >
                <FileText className="w-5 h-5" />
                기록
              </button>
              <button
                onClick={() => setShowSettings(true)}
                className="px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              >
                설정
              </button>
              <motion.button
                onClick={handleLogout}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                로그아웃
              </motion.button>
            </div>
          </div>
        </div>
      </header>

      {/* 진행 표시 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-center gap-4">
          {[1, 2, 3, 4].map((step) => (
            <div key={step} className="flex items-center gap-2">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                  step <= currentStep
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}
              >
                {step}
              </div>
              {step < 4 && (
                <div
                  className={`w-16 h-1 ${
                    step < currentStep ? 'bg-blue-500' : 'bg-gray-700'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnimatePresence mode="wait">
          {/* Step 1: 주제 입력 */}
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold mb-2">Step 1 주제 입력</h2>
                <p className="text-gray-400">어떤 내용의 블로그 글을 작성하고 싶으신가요?</p>
              </div>

              <div className="bg-gray-800 rounded-xl p-6 space-y-6">
                {/* 주제 */}
                <div className="space-y-2">
                  <Label.Root htmlFor="topic" className="text-sm font-medium text-gray-300">
                    주제 *
                  </Label.Root>
                  <p className="text-xs text-gray-500">
                    주제는 구체적일수록 명확한 결과에 도달합니다
                  </p>
                  <p className="text-xs text-yellow-400">
                    ⚠ AI는 최신정보성의 학습이 되어있지 않을 수 있습니다. 입력란에 구체적으로 작성하여야 합니다.
                  </p>
                  <p className="text-xs text-gray-500">
                    (예시: 2025년 정책자금, 오늘일자 뉴스, ...)
                  </p>
                  <input
                    id="topic"
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
                    placeholder="예: 블로그 수익화: 첫 달에 해야 할 7가지"
                  />
                </div>

                {/* 대상 독자 */}
                <div className="space-y-2">
                  <Label.Root htmlFor="targetAudience" className="text-sm font-medium text-gray-300">
                    대상 독자 *
                  </Label.Root>
                  <input
                    id="targetAudience"
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
                    placeholder="예: 초보 블로거 / 취업 준비생"
                  />
                </div>

                {/* 세부 키워드 */}
                <div className="space-y-2">
                  <Label.Root htmlFor="detailedKeywords" className="text-sm font-medium text-gray-300">
                    세부 키워드 (선택사항)
                  </Label.Root>
                  <p className="text-xs text-gray-500">
                    글에 포함하고 싶은 특정 키워드나 용어를 입력하세요. 쉼표(,)로 구분하여 여러 개 입력 가능합니다.
                  </p>
                  <input
                    id="detailedKeywords"
                    type="text"
                    value={detailedKeywords}
                    onChange={(e) => setDetailedKeywords(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400"
                    placeholder="예: SEO 최적화, 구글 애널리틱스, 키워드 리서치"
                  />
                </div>

                {/* 글 의도 */}
                <div className="space-y-2">
                  <Label.Root className="text-sm font-medium text-gray-300">
                    글 의도 (복수 선택 가능)
                  </Label.Root>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                    {(['정보성', '방문후기/여행기', '제품 리뷰/홍보', '튜토리얼', '비교/리뷰', '문제 해결 가이드', '교육/강의', '스토리텔링', '브랜딩', '설득/마케팅', '엔터테인먼트', '맛집', '일상생각', '상품리뷰', '경제비즈니스', 'IT컴퓨터', '교육학문'] as ArticleIntent[]).map((intent) => (
                      <button
                        key={intent}
                        onClick={() => toggleArticleIntent(intent)}
                        className={`px-4 py-2 rounded-lg font-medium transition-all ${
                          articleIntents.includes(intent)
                            ? 'bg-purple-500 text-white'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        {intent}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 톤/스타일 */}
                <div className="space-y-2">
                  <Label.Root className="text-sm font-medium text-gray-300">
                    톤/스타일
                  </Label.Root>
                  <Select.Root value={toneStyle} onValueChange={(value) => setToneStyle(value as ToneStyle)}>
                    <Select.Trigger className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-white flex items-center justify-between">
                      <Select.Value />
                      <Select.Icon>
                        <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                          <path d="M4 6L7.5 9.5L11 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                        </svg>
                      </Select.Icon>
                    </Select.Trigger>
                    <Select.Portal>
                      <Select.Content className="bg-gray-800 border border-gray-600 rounded-lg shadow-lg z-50">
                        <Select.Viewport className="p-2">
                          {(['친절하고 명확하게', '전문적이고 간결하게', '대화체로 친근하게', '유머러스하게', '권위적으로 신뢰감 있게', '감성적이고 따뜻하게', '객관적이고 중립적으로', '열정적이고 동기부여', '비판적이고 분석적으로', '직접 입력'] as ToneStyle[]).map((tone) => (
                            <Select.Item
                              key={tone}
                              value={tone}
                              className="px-4 py-2 hover:bg-gray-700 cursor-pointer text-white rounded-lg outline-none"
                            >
                              <Select.ItemText>{tone}</Select.ItemText>
                            </Select.Item>
                          ))}
                        </Select.Viewport>
                      </Select.Content>
                    </Select.Portal>
                  </Select.Root>
                  {toneStyle === '직접 입력' && (
                    <input
                      type="text"
                      value={customToneStyle}
                      onChange={(e) => setCustomToneStyle(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-400 mt-2"
                      placeholder="톤/스타일을 직접 입력하세요"
                    />
                  )}
                </div>

                {/* 연령층 */}
                <div className="space-y-2">
                  <Label.Root className="text-sm font-medium text-gray-300">
                    연령층 (복수 선택 가능)
                  </Label.Root>
                  <div className="flex flex-wrap gap-3">
                    {(['전체', '10대', '20대', '30대', '40대', '50대', '60대+'] as AgeGroup[]).map((age) => (
                      <button
                        key={age}
                        onClick={() => toggleAgeGroup(age)}
                        className={`px-4 py-2 rounded-full font-medium transition-all ${
                          ageGroups.includes(age)
                            ? 'bg-blue-500 text-white border-2 border-blue-400'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        {age}
                      </button>
                    ))}
                  </div>
                </div>

                {/* 성별 */}
                <div className="space-y-2">
                  <Label.Root className="text-sm font-medium text-gray-300">
                    성별
                  </Label.Root>
                  <div className="flex gap-3">
                    {(['전체', '남성', '여성'] as Gender[]).map((g) => (
                      <button
                        key={g}
                        onClick={() => setGender(g)}
                        className={`px-4 py-2 rounded-full font-medium transition-all ${
                          gender === g
                            ? 'bg-blue-500 text-white border-2 border-blue-400'
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                        }`}
                      >
                        {g}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <motion.button
                  onClick={handleNextToStep2}
                  disabled={!topic.trim() || !targetAudience.trim()}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-8 py-3 bg-white text-gray-900 rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  다음 단계
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </div>
            </motion.div>
          )}

          {/* Step 2: 초안 생성 */}
          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold">Step 2 초안 생성</h2>
                <button
                  onClick={() => {
                    setCurrentStep(1);
                    setShowConfirmStep2(false);
                  }}
                  className="px-4 py-2 text-gray-400 hover:text-white"
                >
                  뒤로가기
                </button>
              </div>

              {showConfirmStep2 && !isGenerating ? (
                <div className="bg-gray-800 rounded-xl p-12 text-center">
                  <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-6 border-2 border-white">
                    <CheckCircle2 className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold mb-4">이제 준비는 끝났습니다!</h3>
                  <p className="text-gray-400 mb-8">
                    입력하신 내용을 바탕으로 ChatGPT, Groq, Gemini를 통해 초안을 작성합니다.
                  </p>
                  <div className="flex justify-center gap-8 mb-8">
                    {['ChatGPT', 'Gemini', 'Groq'].map((model) => (
                      <div key={model} className="text-center">
                        {getModelIcon(model)}
                        <p className="text-sm text-gray-400 mt-2">{model}</p>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-center gap-4">
                    <button
                      onClick={() => {
                        setShowConfirmStep2(false);
                        setCurrentStep(1);
                      }}
                      className="px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium"
                    >
                      뒤로가기
                    </button>
                    <motion.button
                      onClick={handleGenerateDrafts}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="px-6 py-3 bg-white text-gray-900 rounded-lg font-semibold"
                    >
                      시작하기
                    </motion.button>
                  </div>
                </div>
              ) : (
                <>
                  {isGenerating && (
                    <div className="bg-gray-800 rounded-xl p-6 text-center mb-6">
                      <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                      <h3 className="text-xl font-bold mb-2">AI 초안 생성 중</h3>
                      <p className="text-gray-400 text-sm">
                        3개의 AI 모델이 동시에 블로그 초안을 작성하고 있습니다
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {drafts.map((draft, index) => (
                      <motion.div
                        key={draft.model}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={`bg-gray-800 rounded-xl border-2 ${getModelBorderColor(draft.model)} overflow-hidden`}
                      >
                        <div className={`p-4 flex items-center gap-3 ${
                          draft.model === 'ChatGPT' ? 'bg-green-500' :
                          draft.model === 'Gemini' ? 'bg-blue-500' :
                          draft.model === 'Groq' ? 'bg-orange-500' :
                          'bg-gray-500'
                        }`}>
                          {getModelIcon(draft.model)}
                          <h3 className="text-lg font-bold text-white">{draft.model}</h3>
                          {draft.status === 'success' && (
                            <CheckCircle2 className="w-5 h-5 text-white ml-auto" />
                          )}
                          {draft.status === 'generating' && (
                            <Loader2 className="w-5 h-5 text-white ml-auto animate-spin" />
                          )}
                          {draft.status === 'error' && (
                            <span className="text-red-300 ml-auto text-xs">오류</span>
                          )}
                        </div>
                        <div className="p-4">
                          {draft.status === 'generating' ? (
                            <div className="h-80 flex flex-col items-center justify-center">
                              <Loader2 className="w-8 h-8 animate-spin text-gray-400 mb-4" />
                              <p className="text-gray-400 text-sm">생성 중...</p>
                            </div>
                          ) : draft.status === 'error' ? (
                            <div className="h-80 flex flex-col items-center justify-center p-4">
                              <p className="text-red-400 text-sm mb-2 font-semibold">생성 실패</p>
                              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 max-h-48 overflow-y-auto">
                                <p className="text-red-300 text-xs whitespace-pre-wrap break-words">
                                  {draft.error || '알 수 없는 오류가 발생했습니다.'}
                                </p>
                              </div>
                              <p className="text-gray-500 text-xs mt-3">다른 모델의 결과로 진행할 수 있습니다.</p>
                            </div>
                          ) : (
                            <>
                              <div className="h-80 overflow-y-auto mb-4">
                                <h4 className="text-white font-bold text-base mb-3 line-clamp-2">
                                  {draft.content.split('\n').find(line => line.trim().startsWith('#'))?.replace(/^#+\s*/, '') || '초안'}
                                </h4>
                                <div className="text-white text-sm whitespace-pre-wrap leading-relaxed">
                                  {displayedDraftContent[draft.model] || draft.content}
                                </div>
                              </div>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => setSelectedDraft({ model: draft.model, content: draft.content })}
                                  className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                                >
                                  <Edit className="w-4 h-4" />
                                  편집
                                </button>
                                <button
                                  onClick={() => setSelectedDraft({ model: draft.model, content: draft.content })}
                                  className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                                >
                                  <Eye className="w-4 h-4" />
                                  자세히
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {!isGenerating && drafts.some(d => d.status === 'success') && (
                    <div className="mt-6">
                      {drafts.every(d => d.status === 'success') ? (
                        <div className="bg-green-500/20 border border-green-500 rounded-xl p-6 text-center mb-6">
                          <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4" />
                          <h3 className="text-xl font-bold mb-2">생성이 완료되었습니다</h3>
                          <p className="text-gray-400">다음 단계로 넘어갑니다</p>
                        </div>
                      ) : (
                        <div className="bg-yellow-500/20 border border-yellow-500 rounded-xl p-6 text-center mb-6">
                          <CheckCircle2 className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
                          <h3 className="text-xl font-bold mb-2">일부 모델 생성 완료</h3>
                          <p className="text-gray-400">
                            {drafts.filter(d => d.status === 'success').length}개 모델이 성공적으로 생성되었습니다.
                            {drafts.filter(d => d.status === 'error').length > 0 && (
                              <span className="block mt-2 text-yellow-300">
                                {drafts.filter(d => d.status === 'error').length}개 모델에서 오류가 발생했습니다.
                              </span>
                            )}
                          </p>
                        </div>
                      )}
                      <div className="flex justify-end">
                        <motion.button
                          onClick={handleAnalyzeDrafts}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          className="px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold flex items-center gap-2"
                        >
                          분석하기
                          <ArrowRight className="w-5 h-5" />
                        </motion.button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}

          {/* Step 3: 장단점 분석 */}
          {currentStep === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold mb-2">Step 3 장단점 분석</h2>
                  <p className="text-gray-400">각 초안의 장단점을 심층 분석하여 최적의 블로그 글을 만듭니다</p>
                </div>
                <button
                  onClick={() => setCurrentStep(2)}
                  className="px-4 py-2 text-gray-400 hover:text-white"
                >
                  뒤로가기
                </button>
              </div>

              {isAnalyzing ? (
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-8">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-white animate-pulse" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">⚡ 심층 분석 진행중...</h3>
                      <p className="text-white/80">AI가 3개 초안을 분석하고 있습니다</p>
                    </div>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2 mb-4">
                    <motion.div
                      className="bg-white h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: '66%' }}
                      transition={{ duration: 2 }}
                    />
                  </div>
                  <div className="flex gap-4 text-white/80 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-300 rounded-full"></div>
                      장점 분석
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-red-300 rounded-full"></div>
                      단점 파악
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-300 rounded-full"></div>
                      개선 방안
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {analyses.map((analysis, index) => (
                  <motion.div
                    key={analysis.model}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`bg-gray-800 rounded-xl border-2 ${getModelBorderColor(analysis.model)} overflow-hidden`}
                  >
                    <div className={`p-4 flex items-center gap-3 ${
                      analysis.model === 'ChatGPT' ? 'bg-green-500' :
                      analysis.model === 'Gemini' ? 'bg-blue-500' :
                      analysis.model === 'Groq' ? 'bg-orange-500' :
                      'bg-gray-500'
                    }`}>
                      {getModelIcon(analysis.model)}
                      <h3 className="text-lg font-bold text-white">{analysis.model} 분석</h3>
                    </div>
                    <div className="p-4 min-h-[400px] flex flex-col">
                      {analysis.status === 'analyzing' && (
                        <div className="flex items-center justify-center h-full">
                          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                        </div>
                      )}
                      {analysis.status === 'success' && (
                        <>
                          <div className="flex-1 space-y-4 overflow-y-auto">
                            <div>
                              <h4 className="text-sm font-semibold text-green-400 mb-2">1) 주요 장점 (3-5개)</h4>
                              <ul className="space-y-1">
                                {analysis.pros.map((pro, idx) => (
                                  <li key={idx} className="text-white text-sm">• {pro}</li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <h4 className="text-sm font-semibold text-red-400 mb-2">2) 주요 단점 (1-2개)</h4>
                              <ul className="space-y-1">
                                {analysis.cons.map((con, idx) => (
                                  <li key={idx} className="text-white text-sm">• {con}</li>
                                ))}
                              </ul>
                            </div>
                            <div>
                              <h4 className="text-sm font-semibold text-yellow-400 mb-2">3) 개선 방안</h4>
                              <p className="text-white text-sm">{analysis.improvement}</p>
                            </div>
                          </div>
                          <div className="flex gap-2 mt-4 pt-4 border-t border-gray-700">
                            <button
                              onClick={() => {
                                const analysisText = `장점:\n${analysis.pros.map(p => `- ${p}`).join('\n')}\n\n단점:\n${analysis.cons.map(c => `- ${c}`).join('\n')}\n\n개선 방안:\n${analysis.improvement}`;
                                setSelectedDraft({ model: `${analysis.model} 분석`, content: analysisText });
                              }}
                              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                            >
                              <Edit className="w-4 h-4" />
                              편집
                            </button>
                            <button
                              onClick={() => {
                                const analysisText = `# ${analysis.model} 분석\n\n## 1) 주요 장점 (3-5개)\n${analysis.pros.map(p => `- ${p}`).join('\n')}\n\n## 2) 주요 단점 (1-2개)\n${analysis.cons.map(c => `- ${c}`).join('\n')}\n\n## 3) 개선 방안\n${analysis.improvement}`;
                                setSelectedDraft({ model: `${analysis.model} 분석`, content: analysisText });
                              }}
                              className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                            >
                              <Eye className="w-4 h-4" />
                              자세히
                            </button>
                          </div>
                        </>
                      )}
                      {analysis.status === 'error' && (
                        <div className="text-red-400 text-sm">
                          <p className="font-semibold">오류 발생:</p>
                          <p>{analysis.error}</p>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>

              {!isAnalyzing && analyses.some(a => a.status === 'success') && (
                <>
                  {analyses.every(a => a.status === 'success') ? (
                    <div className="bg-green-500/20 border border-green-500 rounded-xl p-6 text-center mb-6">
                      <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4" />
                      <h3 className="text-xl font-bold mb-2">분석이 완료되었습니다!</h3>
                      <p className="text-gray-400">모든 모델의 분석이 완료되었습니다. 최종 글을 생성할 수 있습니다.</p>
                    </div>
                  ) : (
                    <div className="bg-yellow-500/20 border border-yellow-500 rounded-xl p-6 text-center mb-6">
                      <CheckCircle2 className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
                      <h3 className="text-xl font-bold mb-2">일부 분석 완료</h3>
                      <p className="text-gray-400">
                        {analyses.filter(a => a.status === 'success').length}개 모델의 분석이 완료되었습니다.
                        {analyses.filter(a => a.status === 'error').length > 0 && (
                          <span className="block mt-2 text-yellow-300">
                            {analyses.filter(a => a.status === 'error').length}개 모델에서 오류가 발생했습니다.
                          </span>
                        )}
                      </p>
                    </div>
                  )}
                  <div className="flex justify-end">
                    <motion.button
                      onClick={handleGenerateFinal}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-semibold flex items-center gap-2"
                    >
                      최종 글 생성하기
                      <ArrowRight className="w-5 h-5" />
                    </motion.button>
                  </div>
                </>
              )}
            </motion.div>
          )}

          {/* Step 4: 최종 생성 */}
          {currentStep === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-3xl font-bold mb-2">Step 4 최종 생성</h2>
                <p className="text-gray-400">세 모델의 강점을 조합해 고품질 글로 완성합니다.</p>
              </div>

              {isGeneratingFinal ? (
                <div className="space-y-6">
                  <div className="text-center mb-6">
                    <div className="w-24 h-24 mx-auto mb-4 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center transform rotate-45">
                      <div className="transform -rotate-45">
                        <Sparkles className="w-12 h-12 text-white" />
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-purple-400 mb-2">
                      AI가 최고의 고품격 블로그 콘텐츠를 생성합니다
                    </h3>
                    <p className="text-gray-400">
                      3개 초안과 전문가 분석을 통합하여 완벽한 최종 글을 만듭니다
                    </p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-8">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                        <Loader2 className="w-6 h-6 text-white animate-spin" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-yellow-400">최고 품질의 콘텐츠 생성 중...</h3>
                        <p className="text-white">AI가 3개 초안의 장점을 통합하고 있습니다</p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 mb-4">
                      <motion.div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: '66%' }}
                        transition={{ duration: 2 }}
                      />
                    </div>
                    <div className="flex gap-4 text-gray-300 text-sm">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                        초안 통합
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-pink-400 rounded-full"></div>
                        SEO 최적화
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-pink-400 rounded-full"></div>
                        품질 검증
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-6 border-2 border-purple-500">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">최종 블로그 글</h3>
                        <p className="text-gray-400 text-sm">고품질 SEO 최적화 콘텐츠</p>
                      </div>
                    </div>
                    <div className="bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-lg p-4 min-h-[200px] flex items-center justify-center">
                      <div className="w-2 h-6 bg-white animate-pulse"></div>
                    </div>
                  </div>
                </div>
              ) : finalContent ? (
                <div className="space-y-6">
                  <div className="bg-gray-800 rounded-xl p-6 border-2 border-purple-500">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center">
                        <Sparkles className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">최종 블로그 글</h3>
                        <p className="text-gray-400 text-sm">고품질 SEO 최적화 콘텐츠</p>
                      </div>
                    </div>
                    <div className="bg-gray-900 rounded-lg p-6 min-h-[400px] max-h-[600px] overflow-y-auto">
                      <div className="prose prose-invert max-w-none">
                        <div className="text-white text-sm leading-relaxed whitespace-pre-wrap">
                          {(displayedFinalContent || finalContent).split('\n').map((line, idx) => {
                            if (line.startsWith('## ')) {
                              return <h2 key={idx} className="text-xl font-bold mt-6 mb-3 text-white">{line.replace(/^##\s*/, '')}</h2>;
                            } else if (line.startsWith('### ')) {
                              return <h3 key={idx} className="text-lg font-semibold mt-4 mb-2 text-white">{line.replace(/^###\s*/, '')}</h3>;
                            } else if (line.startsWith('# ')) {
                              return <h1 key={idx} className="text-2xl font-bold mt-4 mb-4 text-white">{line.replace(/^#\s*/, '')}</h1>;
                            } else if (line.trim().startsWith('|')) {
                              return <div key={idx} className="my-4 overflow-x-auto"><pre className="text-xs text-gray-300">{line}</pre></div>;
                            } else if (line.trim() === '') {
                              return <br key={idx} />;
                            } else if (line.trim().startsWith('- ')) {
                              return <li key={idx} className="ml-4 mb-1">{line.replace(/^-\s*/, '')}</li>;
                            } else {
                              return <p key={idx} className="mb-3">{line}</p>;
                            }
                          })}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 복사 버튼들 */}
                  <div className="flex flex-wrap gap-3 justify-center">
                    <motion.button
                      onClick={() => {
                        navigator.clipboard.writeText(finalContent);
                        alert('복사되었습니다!');
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold flex items-center gap-2"
                    >
                      <Copy className="w-5 h-5" />
                      복사하기
                    </motion.button>
                    <motion.button
                      onClick={() => {
                        const htmlContent = finalContent
                          .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                          .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                          .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/^-\s+(.*)$/gim, '<li>$1</li>')
                          .replace(/\n\n/g, '</p><p>')
                          .replace(/^(.+)$/gim, '<p>$1</p>');
                        navigator.clipboard.writeText(htmlContent);
                        alert('HTML이 복사되었습니다!');
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-semibold flex items-center gap-2"
                    >
                      <Code className="w-5 h-5" />
                      HTML 복사
                    </motion.button>
                    <motion.button
                      onClick={() => {
                        // 네이버 블로그 형식으로 변환
                        let naverContent = finalContent;
                        
                        // 제목 처리
                        naverContent = naverContent.replace(/^# (.*$)/gim, '<h1>$1</h1>');
                        
                        // 소제목 처리
                        naverContent = naverContent.replace(/^## (.*$)/gim, '<h2>$1</h2>');
                        naverContent = naverContent.replace(/^### (.*$)/gim, '<h3>$1</h3>');
                        
                        // 강조 처리
                        naverContent = naverContent.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                        naverContent = naverContent.replace(/\*(.*?)\*/g, '<i>$1</i>');
                        
                        // 불릿 포인트 처리
                        naverContent = naverContent.replace(/^-\s+(.*)$/gim, '<li>$1</li>');
                        naverContent = naverContent.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
                        
                        // 표 처리 (간단한 마크다운 표)
                        naverContent = naverContent.replace(/\|(.+)\|/g, (match) => {
                          const cells = match.split('|').filter(c => c.trim());
                          return '<table><tr>' + cells.map(c => `<td>${c.trim()}</td>`).join('') + '</tr></table>';
                        });
                        
                        // 문단 처리
                        const paragraphs = naverContent.split(/\n\n+/);
                        naverContent = paragraphs.map(p => {
                          p = p.trim();
                          if (!p || p.startsWith('<')) return p;
                          return `<p>${p}</p>`;
                        }).join('\n');
                        
                        navigator.clipboard.writeText(naverContent);
                        alert('네이버 블로그 형식으로 복사되었습니다!');
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg font-semibold flex items-center gap-2"
                    >
                      <span className="text-lg font-bold">N</span>
                      블로그 복사
                    </motion.button>
                    <motion.button
                      onClick={() => {
                        setCurrentStep(1);
                        setFinalContent('');
                        setDrafts([
                          { model: 'ChatGPT', content: '', status: 'idle' },
                          { model: 'Gemini', content: '', status: 'idle' },
                          { model: 'Groq', content: '', status: 'idle' },
                        ]);
                        setAnalyses([
                          { model: 'ChatGPT', pros: [], cons: [], improvement: '', status: 'idle' },
                          { model: 'Gemini', pros: [], cons: [], improvement: '', status: 'idle' },
                          { model: 'Groq', pros: [], cons: [], improvement: '', status: 'idle' },
                        ]);
                        setTopic('');
                        setTargetAudience('');
                        setDetailedKeywords('');
                        setArticleIntents([]);
                        setToneStyle('친절하고 명확하게');
                        setCustomToneStyle('');
                        setAgeGroups(['전체']);
                        setGender('전체');
                      }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="px-6 py-3 bg-gray-800 border-2 border-purple-500 text-purple-400 rounded-lg font-semibold flex items-center gap-2"
                    >
                      <Home className="w-5 h-5" />
                      처음으로
                    </motion.button>
                  </div>
                </div>
              ) : null}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* 모달: 초안 상세 보기 */}
      <AnimatePresence>
        {selectedDraft && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setSelectedDraft(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              <div               className={`p-4 flex items-center justify-between ${
                selectedDraft.model === 'ChatGPT' ? 'bg-green-500' :
                selectedDraft.model === 'Gemini' ? 'bg-blue-500' :
                selectedDraft.model === 'Groq' ? 'bg-orange-500' :
                'bg-gray-500'
              }`}>
                <div className="flex items-center gap-3">
                  {getModelIcon(selectedDraft.model)}
                  <h3 className="text-lg font-bold text-white">{selectedDraft.model}</h3>
                </div>
                <button
                  onClick={() => setSelectedDraft(null)}
                  className="text-white hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
              <div className="p-6 overflow-y-auto flex-1 bg-gray-50">
                <div className="prose max-w-none">
                  <div className="whitespace-pre-wrap text-sm text-gray-800 font-sans leading-relaxed">
                    {(displayedDraftContent[selectedDraft.model] || selectedDraft.content).split('\n').map((line, idx) => {
                      if (line.startsWith('##')) {
                        return <h2 key={idx} className="text-xl font-bold mt-6 mb-3 text-gray-900">{line.replace(/^##\s*/, '')}</h2>;
                      } else if (line.startsWith('#')) {
                        return <h1 key={idx} className="text-2xl font-bold mt-4 mb-4 text-gray-900">{line.replace(/^#\s*/, '')}</h1>;
                      } else if (line.trim() === '') {
                        return <br key={idx} />;
                      } else {
                        return <p key={idx} className="mb-3">{line}</p>;
                      }
                    })}
                  </div>
                </div>
              </div>
              <div className="p-4 border-t border-gray-200 flex justify-end gap-3">
                <button
                  onClick={() => setSelectedDraft(null)}
                  className="px-6 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-gray-800 font-medium"
                >
                  취소
                </button>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(selectedDraft.content);
                    alert('복사되었습니다!');
                  }}
                  className="px-6 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white font-medium"
                >
                  저장
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 플로팅 메뉴 버튼 */}
      {showFloatingMenu && (
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0 }}
          className="fixed bottom-6 left-6 z-40"
        >
          {/* 메뉴 아이템들 */}
          <AnimatePresence>
            {isFloatingMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="mb-4 space-y-2"
              >
                <motion.button
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  onClick={() => {
                    setShowSettings(true);
                    setIsFloatingMenuOpen(false);
                  }}
                  className="w-12 h-12 bg-gray-800 hover:bg-gray-700 rounded-full flex items-center justify-center shadow-lg border-2 border-gray-600"
                  title="설정"
                >
                  <Sparkles className="w-5 h-5 text-white" />
                </motion.button>
                <motion.button
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 }}
                  onClick={() => {
                    setShowHistory(true);
                    setIsFloatingMenuOpen(false);
                  }}
                  className="w-12 h-12 bg-indigo-600 hover:bg-indigo-700 rounded-full flex items-center justify-center shadow-lg border-2 border-indigo-400"
                  title="기록 보기"
                >
                  <FileText className="w-5 h-5 text-white" />
                </motion.button>
                <motion.button
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  onClick={() => {
                    setCurrentStep(1);
                    setIsFloatingMenuOpen(false);
                  }}
                  className="w-12 h-12 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center shadow-lg"
                  title="처음으로"
                >
                  <Home className="w-5 h-5 text-white" />
                </motion.button>
                <motion.button
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 }}
                  onClick={() => {
                    alert('빠른 생성 기능은 준비 중입니다.');
                    setIsFloatingMenuOpen(false);
                  }}
                  className="w-12 h-12 bg-purple-600 hover:bg-purple-700 rounded-full flex items-center justify-center shadow-lg"
                  title="빠른 생성"
                >
                  <Zap className="w-5 h-5 text-white" />
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 메인 토글 버튼 */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsFloatingMenuOpen(!isFloatingMenuOpen)}
            className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-shadow"
            title={isFloatingMenuOpen ? "메뉴 닫기" : "메뉴 열기"}
          >
            {isFloatingMenuOpen ? (
              <X className="w-6 h-6 text-white" />
            ) : (
              <Menu className="w-6 h-6 text-white" />
            )}
          </motion.button>
        </motion.div>
      )}

      {/* 플로팅 메뉴 표시/숨김 토글 버튼 (항상 표시) */}
      <motion.button
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => {
          const newState = !showFloatingMenu;
          setShowFloatingMenu(newState);
          localStorage.setItem('floating_menu_visible', String(newState));
          setIsFloatingMenuOpen(false);
        }}
        className="fixed bottom-6 left-20 z-40 w-10 h-10 bg-gray-700 hover:bg-gray-600 rounded-full flex items-center justify-center shadow-lg border-2 border-gray-500"
        title={showFloatingMenu ? "메뉴 숨기기" : "메뉴 보이기"}
      >
        {showFloatingMenu ? (
          <ChevronDown className="w-5 h-5 text-white" />
        ) : (
          <ChevronUp className="w-5 h-5 text-white" />
        )}
      </motion.button>
    </div>
  );
}
