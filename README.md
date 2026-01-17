# Multi-LLM 블로그 자동화 시스템

최고의 블로그 AI 에이전트 - 모든 AI 모델을 통합하여 최고의 컨텐츠 생성

## 기술 스택

### Frontend
- Next.js 15
- React 19
- Framer Motion
- Tailwind CSS
- Radix UI Components
- Lucide React (아이콘)

### Backend
- FastAPI (Python)
- 노션 인증
- Multi-LLM 통합 (OpenAI, Groq, Gemini)

### Desktop App
- Electron

## 필수 요구사항

- **Node.js 18 이상** (https://nodejs.org/)
- **Python 3.8 이상** (https://www.python.org/)
  - 설치 시 "Add Python to PATH" 옵션 체크 필수!

## 설치 방법

### 방법 1: 자동 설치 (권장) ⭐

```bash
install.bat
```

이 스크립트가 Frontend와 Backend 패키지를 모두 설치합니다.

### 방법 2: 수동 설치

#### Frontend 설치
```bash
npm install
```
또는 `install_frontend.bat` 실행

#### Backend 설치
```bash
cd backend
pip install -r requirements.txt
cd ..
```
또는 `install_backend.bat` 실행

### API 키 생성 방법

각 AI 모델의 API 키를 생성하는 방법입니다. **앱 내 설정 페이지에서도 입력할 수 있습니다.**

#### 1. OpenAI GPT-5 Nano (30K 토큰)

1. [OpenAI 플랫폼](https://platform.openai.com)에 로그인
2. [API Keys](https://platform.openai.com/api-keys) 메뉴로 이동
3. "Create new secret key" 버튼 클릭
4. 생성된 키를 복사 (형식: `sk-...`)
5. 앱의 설정 페이지 또는 `backend/.env` 파일에 입력

#### 2. Groq (Llama 3.3 70B) (32K 토큰)

1. [Groq Console](https://console.groq.com)에 로그인
2. [API Keys](https://console.groq.com/keys) 메뉴로 이동
3. "Create API Key" 버튼 클릭
4. 생성된 키를 복사 (형식: `gsk_...`)
5. 앱의 설정 페이지 또는 `backend/.env` 파일에 입력

> 💡 **Groq의 장점**: 매우 빠른 추론 속도로 유명합니다. Llama 3.3 70B 모델을 사용합니다.

#### 3. Google Gemini 2.5 Flash-Lite (8K 토큰)

1. [Google AI Studio](https://aistudio.google.com)에 로그인
2. "Get API key" 버튼 클릭
3. 프로젝트 선택 또는 새 프로젝트 생성
4. 생성된 키를 복사 (형식: `AIza...`)
5. 앱의 설정 페이지 또는 `backend/.env` 파일에 입력

### 환경 변수 설정 (필수: Notion API 키)

**⚠️ 중요**: 다른 컴퓨터에서 클론한 경우, `backend/.env` 파일을 생성해야 합니다.

`backend/env.example` 파일을 참고하여 `backend/.env` 파일을 생성하세요:

1. `backend/env.example` 파일을 복사
2. `backend/.env` 파일로 이름 변경
3. 실제 API 키로 값 변경

**필수 설정 (Notion)**:
```env
# 로그인 인증용 Notion API 키 및 Database ID
NOTION_API_KEY=your_notion_login_api_key_here
NOTION_DATABASE_ID=your_notion_login_database_id_here

# 글 저장용 Notion API 키 및 Database ID
ARTICLE_NOTION_API_KEY=your_notion_article_api_key_here
ARTICLE_DATABASE_ID=your_notion_article_database_id_here
```

**선택 설정 (LLM API 키)**:
```env
# LLM API Keys (앱 내 설정 페이지에서도 입력 가능)
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

> 💡 **참고**: 
> - Notion API 키는 **필수**입니다 (로그인 및 글 저장 기능에 필요).
> - LLM API 키는 선택사항입니다. 앱 내 설정 페이지에서 입력하는 것이 더 편리합니다.
> - 사용할 모델의 API 키만 설정하면 됩니다.
> - 모든 모델의 키를 입력하면 3개 모델을 동시에 사용할 수 있습니다.

## 실행 방법

### 방법 1: 자동 실행 (권장) ⭐

```bash
start.bat
```

이 스크립트가 Backend와 Frontend 서버를 자동으로 시작합니다.

### 방법 2: 수동 실행

1. **Backend 시작** (터미널 1)
```bash
cd backend
python main.py
```

2. **Frontend 시작** (터미널 2)
```bash
npm run dev
```

3. **Electron 시작** (터미널 3, 선택사항)
```bash
npm run electron:dev
```

브라우저에서 `http://localhost:3000` 접속

### 프로덕션 빌드

```bash
# Next.js 빌드
npm run build

# Electron 앱 빌드
npm run electron:build
```

## 주요 기능

1. **노션 기반 인증**: 안전한 로그인 시스템
2. **Multi-LLM 지원**: OpenAI, Claude, Gemini 모델 선택 가능
3. **제목 생성**: 키워드 기반 SEO 최적화 제목 생성
4. **본문 생성**: 제목 기반 고품질 블로그 본문 생성
5. **실시간 로그**: 생성 과정 실시간 모니터링

## 문제 해결

### ❌ "ModuleNotFoundError: No module named 'fastapi'"

**해결 방법:**
```bash
install_backend.bat
```
또는
```bash
cd backend
pip install -r requirements.txt
```

### ❌ "'next'은(는) 내부 또는 외부 명령"

**해결 방법:**
```bash
install_frontend.bat
```
또는
```bash
npm install
```

### ❌ "python이 인식되지 않습니다"

**해결 방법:**
1. Python 재설치 시 "Add Python to PATH" 옵션 체크
2. 또는 Python 전체 경로 사용: `C:\Python3x\python.exe -m pip install ...`

### ❌ "npm이 인식되지 않습니다"

**해결 방법:**
- Node.js 설치: https://nodejs.org/
- 설치 후 터미널 재시작

### 입력창 텍스트가 잘 안 보이는 경우

`app/globals.css` 파일에서 입력창 텍스트 색상이 설정되어 있습니다. 다크모드에서도 잘 보이도록 최적화되어 있습니다.

### 백엔드 연결 오류

1. 백엔드가 실행 중인지 확인 (`http://localhost:8000`)
2. CORS 설정 확인
3. 환경 변수가 올바르게 설정되었는지 확인

## 라이선스

MIT
