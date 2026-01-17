# Vercel + Fly.io 배포 가이드

## 📋 사전 준비

1. GitHub 계정 (코드가 GitHub에 올라가 있어야 함)
2. Vercel 계정 (GitHub로 가입)
3. Fly.io 계정 (GitHub로 가입)

---

## 🎨 1단계: Vercel로 프론트엔드(Next.js) 배포

### 1. Vercel 가입 및 프로젝트 생성

1. **Vercel 접속**: https://vercel.com
2. **"Sign Up"** 클릭 → GitHub 계정으로 가입
3. **"Add New..." → "Project"** 클릭
4. GitHub 레포지토리 선택 (`멀티 자동화` 또는 해당 레포지토리)
5. **프로젝트 설정**:
   - **Framework Preset**: Next.js (자동 감지됨)
   - **Root Directory**: `./` (또는 프론트엔드가 있는 폴더)
   - **Build Command**: `npm run build` (자동)
   - **Output Directory**: `.next` (자동)
   - **Install Command**: `npm install` (자동)

### 2. 환경 변수 설정 (선택사항)

Vercel 대시보드에서:
- **Settings → Environment Variables**
- 필요한 경우 추가 (예: `NEXT_PUBLIC_API_URL`)

### 3. 배포 실행

- **"Deploy"** 버튼 클릭
- 자동으로 빌드 및 배포 시작
- 완료되면 `https://your-project.vercel.app` 같은 URL 제공

### 4. 배포 확인

- 배포 완료 후 제공된 URL로 접속
- 정상 작동 확인

**✅ 프론트엔드 배포 완료!**
- Vercel URL 예시: `https://multi-llm-blog-automation.vercel.app`

---

## 🚀 2단계: Fly.io로 백엔드(FastAPI) 배포

### 1. Fly.io CLI 설치

**Windows:**
1. PowerShell 관리자 권한으로 실행
2. 다음 명령어 실행:
```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

또는 공식 웹사이트에서 다운로드:
- https://fly.io/docs/getting-started/installing-flyctl/

**확인:**
```bash
flyctl version
```

### 2. Fly.io 로그인

```bash
flyctl auth login
```
- 브라우저가 열리면 GitHub로 로그인

### 3. Fly.io 앱 생성

```bash
cd backend
flyctl launch
```

질문에 답변:
- **App name**: `ynk-blog-automation-backend` (또는 원하는 이름)
- **Region**: `icn` (서울) 또는 가까운 지역 선택
- **PostgreSQL**: `n` (사용 안 함)
- **Redis**: `n` (사용 안 함)

### 4. `fly.toml` 파일 수정

생성된 `backend/fly.toml` 파일을 수정:

```toml
app = "ynk-blog-automation-backend"
primary_region = "icn"

[build]

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.http_checks]]
    interval = "10s"
    grace_period = "5s"
    method = "GET"
    path = "/"
    protocol = "http"
    timeout = "2s"
    tls_skip_verify = false

    [services.http_checks.headers]
```

### 5. `Dockerfile` 생성 (백엔드)

`backend/Dockerfile` 파일 생성:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 설정
ENV PORT=8000
EXPOSE 8000

# 애플리케이션 실행
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

### 6. `.dockerignore` 생성 (백엔드)

`backend/.dockerignore` 파일 생성:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.pytest_cache
.coverage
.env
.venv
venv/
```

### 7. 환경 변수 설정

```bash
# Fly.io 대시보드에서 설정하거나 CLI로 설정
flyctl secrets set OPENAI_API_KEY=your-key-here
flyctl secrets set GROQ_API_KEY=your-key-here
flyctl secrets set GEMINI_API_KEY=your-key-here
```

### 8. 배포 실행

```bash
flyctl deploy
```

- 빌드 및 배포 시작
- 완료되면 `https://ynk-blog-automation-backend.fly.dev` 같은 URL 제공

### 9. 배포 확인

```bash
# 앱 상태 확인
flyctl status

# 로그 확인
flyctl logs

# URL로 API 테스트
curl https://ynk-blog-automation-backend.fly.dev/
```

**✅ 백엔드 배포 완료!**
- Fly.io URL 예시: `https://ynk-blog-automation-backend.fly.dev`

---

## 🔗 3단계: CORS 설정 변경

### 백엔드 `main.py` 수정

배포된 Vercel URL을 CORS 허용 목록에 추가:

```python
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-project.vercel.app",  # 배포된 Vercel URL 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

변경 후 다시 배포:
```bash
cd backend
flyctl deploy
```

---

## 🌐 4단계: 프론트엔드에서 백엔드 URL 변경

### 옵션 1: 환경 변수 사용 (권장)

`.env.local` 파일 생성 (프로젝트 루트):
```
NEXT_PUBLIC_API_URL=https://ynk-blog-automation-backend.fly.dev
```

Vercel 대시보드에서 환경 변수 추가:
- **Settings → Environment Variables**
- `NEXT_PUBLIC_API_URL` = `https://ynk-blog-automation-backend.fly.dev`

### 옵션 2: 코드에서 직접 변경

프론트엔드 코드에서 API URL을 하드코딩:

```typescript
// 예: MainPage.tsx, LoginPage.tsx 등
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ynk-blog-automation-backend.fly.dev';

// 사용 예시
const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
  // ...
});
```

모든 `http://localhost:8000`을 환경 변수나 배포된 URL로 변경

---

## ✅ 5단계: 최종 확인

### 1. 프론트엔드 접속
- Vercel URL로 접속
- 로그인 테스트

### 2. 백엔드 API 테스트
```bash
# 헬스 체크
curl https://ynk-blog-automation-backend.fly.dev/

# 로그인 테스트
curl -X POST https://ynk-blog-automation-backend.fly.dev/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","user_pw":"test"}'
```

### 3. 통합 테스트
- Vercel에서 로그인
- 초안 생성 테스트
- 최종글 생성 테스트
- 모든 기능 정상 작동 확인

---

## 📊 배포 후 관리

### Fly.io 명령어

```bash
# 앱 상태 확인
flyctl status

# 로그 실시간 확인
flyctl logs

# 앱 재시작
flyctl apps restart ynk-blog-automation-backend

# 환경 변수 확인
flyctl secrets list

# 환경 변수 추가/수정
flyctl secrets set KEY=value

# 앱 삭제 (필요시)
flyctl apps destroy ynk-blog-automation-backend
```

### Vercel 명령어

```bash
# Vercel CLI 설치
npm i -g vercel

# 로그인
vercel login

# 배포
vercel

# 프로덕션 배포
vercel --prod

# 환경 변수 추가
vercel env add NEXT_PUBLIC_API_URL
```

---

## 🎯 최종 URL 예시

- **프론트엔드**: `https://multi-llm-blog-automation.vercel.app`
- **백엔드**: `https://ynk-blog-automation-backend.fly.dev`

---

## 💡 문제 해결

### 백엔드가 응답하지 않을 때
1. `flyctl status`로 앱 상태 확인
2. `flyctl logs`로 에러 확인
3. 포트 설정 확인 (`fly.toml`의 `internal_port`)

### CORS 에러 발생 시
1. 백엔드 `main.py`의 `allow_origins`에 Vercel URL이 있는지 확인
2. `https://` 프로토콜 포함 여부 확인
3. 변경 후 재배포

### 환경 변수 문제
1. Fly.io: `flyctl secrets list`로 확인
2. Vercel: 대시보드에서 확인
3. 환경 변수 이름 정확히 확인 (`NEXT_PUBLIC_` 접두사 필요)

---

## 📝 체크리스트

- [ ] Vercel 계정 생성 및 프로젝트 배포
- [ ] Fly.io CLI 설치 및 로그인
- [ ] Fly.io 앱 생성 및 배포
- [ ] 백엔드 `main.py` CORS 설정 변경
- [ ] 프론트엔드 API URL 변경
- [ ] 환경 변수 설정
- [ ] 통합 테스트 완료

---

**🎉 완료! 이제 무료로 웹에서 사용 가능합니다!**
