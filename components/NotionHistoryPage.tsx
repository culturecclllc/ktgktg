'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Copy, Code, Calendar, FileText, Loader2, RefreshCw } from 'lucide-react';

interface NotionHistoryPageProps {
  onBack: () => void;
}

interface NotionArticle {
  id: string;
  title: string;
  topic?: string;
  content: string;
  created_date: string;
  model?: string;
  article_intent?: string;
  target_audience?: string;
  // 추가 필드가 있으면 여기에 추가
  [key: string]: any;
}

export default function NotionHistoryPage({ onBack }: NotionHistoryPageProps) {
  const [articles, setArticles] = useState<NotionArticle[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedArticle, setSelectedArticle] = useState<NotionArticle | null>(null);

  useEffect(() => {
    fetchArticles();
  }, []);

  const fetchArticles = async () => {
    setIsLoading(true);
    setError('');
    try {
      // TODO: 여기에 새로운 Notion API 엔드포인트 URL을 입력하세요
      // 예: 'http://localhost:8000/api/notion/articles'
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/history/articles`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // API 응답 형식에 맞게 수정하세요
        // 예: data.articles, data.data, data.results 등
        setArticles(data.articles || data.data || data.results || []);
        // 첫 번째 글을 기본으로 선택
        const articlesList = data.articles || data.data || data.results || [];
        if (articlesList.length > 0) {
          setSelectedArticle(articlesList[0]);
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: '기록을 불러오는데 실패했습니다.' }));
        setError(errorData.detail || errorData.message || '기록을 불러오는데 실패했습니다.');
      }
    } catch (err) {
      setError('서버에 연결할 수 없습니다.');
      console.error('Fetch articles error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return '날짜 없음';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const formatDateShort = (dateString: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('복사되었습니다!');
  };

  const copyAsHTML = (content: string, title: string) => {
    const html = `<h1>${title}</h1>\n${content.split('\n').map(line => {
      if (line.startsWith('##')) {
        return `<h2>${line.replace(/^##\s*/, '')}</h2>`;
      } else if (line.startsWith('#')) {
        return `<h1>${line.replace(/^#\s*/, '')}</h1>`;
      } else {
        return `<p>${line}</p>`;
      }
    }).join('\n')}`;
    navigator.clipboard.writeText(html);
    alert('HTML 형식으로 복사되었습니다!');
  };

  const copyAsNaverBlog = (content: string, title: string) => {
    let naverContent = content;
    naverContent = naverContent.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
    naverContent = naverContent.replace(/^##\s+(.+)$/gm, '<h2>$1</h2>');
    naverContent = naverContent.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
    naverContent = naverContent.split('\n').map(line => {
      if (line.trim() === '') return '<br>';
      if (line.startsWith('<h')) return line;
      return `<p>${line}</p>`;
    }).join('\n');
    
    navigator.clipboard.writeText(naverContent);
    alert('네이버 블로그 형식으로 복사되었습니다!');
  };

  const extractTags = (content: string): string[] => {
    const tagRegex = /#([가-힣a-zA-Z0-9_]+)/g;
    const matches = content.match(tagRegex);
    return matches ? matches.map(tag => tag.replace('#', '')) : [];
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 헤더 */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={onBack}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              돌아가기
            </button>
            <h1 className="text-2xl font-bold text-white">Notion 기록</h1>
            <button
              onClick={fetchArticles}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              새로고침
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* 왼쪽 사이드바 */}
          <div className="w-80 flex-shrink-0">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-4">내글</h2>
              <p className="text-gray-400 text-sm mb-6">
                총 {articles.length}개의 글을 작성했습니다
              </p>
              
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">글 목록</h3>
                
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                  </div>
                ) : error ? (
                  <div className="text-red-400 text-sm py-4">{error}</div>
                ) : articles.length === 0 ? (
                  <div className="text-gray-400 text-sm py-4">작성한 글이 없습니다.</div>
                ) : (
                  <div className="space-y-3">
                    {articles.map((article) => (
                      <motion.div
                        key={article.id}
                        onClick={() => setSelectedArticle(article)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                          selectedArticle?.id === article.id
                            ? 'border-purple-500 bg-purple-500/10'
                            : 'border-gray-700 bg-gray-700/30 hover:border-gray-600'
                        }`}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <h4 className="text-white font-medium mb-2 line-clamp-2">
                          {article.title || article.topic || '제목 없음'}
                        </h4>
                        <p className="text-gray-400 text-xs">
                          {formatDateShort(article.created_date || article.createdDate || article.date)}
                        </p>
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 오른쪽 메인 컨텐츠 */}
          <div className="flex-1">
            {selectedArticle ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800 rounded-lg p-8 border border-gray-700"
              >
                {/* 제목 및 메타 정보 */}
                <div className="mb-6">
                  <div className="bg-white rounded-lg p-4 mb-4">
                    <h1 className="text-2xl font-bold text-gray-900 mb-2">
                      {selectedArticle.title || selectedArticle.topic || '제목 없음'}
                    </h1>
                    <p className="text-gray-600 text-sm">
                      {formatDateShort(selectedArticle.created_date || selectedArticle.createdDate || selectedArticle.date)}
                    </p>
                  </div>
                  
                  <div className="flex items-center justify-between mb-6">
                    <div className="text-gray-400 text-sm">
                      작성: {formatDate(selectedArticle.created_date || selectedArticle.createdDate || selectedArticle.date)}
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => copyToClipboard(selectedArticle.content)}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <Copy className="w-4 h-4" />
                        복사
                      </button>
                      <button
                        onClick={() => copyAsHTML(selectedArticle.content, selectedArticle.title || selectedArticle.topic || '')}
                        className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <Code className="w-4 h-4" />
                        {'</>'} HTML
                      </button>
                      <button
                        onClick={() => copyAsNaverBlog(selectedArticle.content, selectedArticle.title || selectedArticle.topic || '')}
                        className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                      >
                        <span className="text-lg font-bold">N</span>
                        블로그
                      </button>
                    </div>
                  </div>
                </div>

                {/* 글 내용 */}
                <div className="prose prose-invert max-w-none mb-8">
                  <div className="whitespace-pre-wrap text-gray-300 leading-relaxed text-base">
                    {selectedArticle.content || '내용이 없습니다.'}
                  </div>
                </div>

                {/* 태그 */}
                {selectedArticle.content && (
                  <div className="mb-8 pt-6 border-t border-gray-700">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-gray-400 mr-2">태그:</span>
                      {extractTags(selectedArticle.content).map((tag, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-gray-700 text-gray-300 rounded-full text-sm"
                        >
                          #{tag}
                        </span>
                      ))}
                      {extractTags(selectedArticle.content).length === 0 && (
                        <span className="text-gray-500 text-sm">태그가 없습니다.</span>
                      )}
                    </div>
                  </div>
                )}

                {/* 하단 복사 버튼들 */}
                <div className="flex gap-3 justify-end pt-6 border-t border-gray-700">
                  <button
                    onClick={() => copyToClipboard(selectedArticle.content)}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <Copy className="w-5 h-5" />
                    복사하기
                  </button>
                  <button
                    onClick={() => copyAsHTML(selectedArticle.content, selectedArticle.title || selectedArticle.topic || '')}
                    className="px-6 py-3 bg-pink-600 hover:bg-pink-700 text-white rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <Code className="w-5 h-5" />
                    {'</>'} HTML 복사
                  </button>
                  <button
                    onClick={() => copyAsNaverBlog(selectedArticle.content, selectedArticle.title || selectedArticle.topic || '')}
                    className="px-6 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                  >
                    <span className="text-lg font-bold">N</span>
                    블로그 복사
                  </button>
                </div>
              </motion.div>
            ) : (
              <div className="bg-gray-800 rounded-lg p-12 border border-gray-700 text-center">
                <FileText className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">글을 선택해주세요.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
