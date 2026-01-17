# GitHub 레포지토리에 코드 업로드 가이드

## 📋 사전 준비

### 1. Git 설치 확인

**Windows PowerShell에서 확인:**
```powershell
git --version
```

**Git이 없으면:**
- https://git-scm.com/download/win 에서 다운로드
- 기본 설정으로 설치 진행

---

## 🚀 방법 1: 기존 프로젝트를 GitHub에 푸시 (권장)

### 1단계: 프로젝트 폴더로 이동

**PowerShell 또는 명령 프롬프트에서:**
```bash
cd "C:\Users\OoOoO\서이추\멀티 자동화"
```

### 2단계: Git 초기화 (아직 안 했다면)

```bash
git init
```

### 3단계: 모든 파일 추가

```bash
git add .
```

### 4단계: 첫 커밋 생성

```bash
git commit -m "Initial commit: Multi-LLM 블로그 자동화 프로젝트"
```

### 5단계: GitHub 레포지토리 연결

**GitHub 페이지에서 보이는 URL 사용:**
```bash
git remote add origin https://github.com/culturecclllc/ktgktg.git
```

**이미 연결되어 있다면:**
```bash
git remote set-url origin https://github.com/culturecclllc/ktgktg.git
```

### 6단계: 메인 브랜치로 이름 변경 (선택사항)

```bash
git branch -M main
```

### 7단계: GitHub에 푸시

```bash
git push -u origin main
```

**첫 푸시 시 GitHub 로그인 창이 열림**
- 브라우저에서 GitHub 로그인
- 권한 승인

---

## 🔐 GitHub 인증 (문제 발생 시)

### Personal Access Token 사용

1. **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. **"Generate new token (classic)"** 클릭
3. **권한 선택**:
   - `repo` (모든 항목 체크)
4. **"Generate token"** 클릭
5. **토큰 복사** (한 번만 보임!)

**Windows에서 자격 증명 저장:**
```bash
git config --global credential.helper wincred
```

**푸시 시:**
- Username: GitHub 사용자명
- Password: Personal Access Token 입력

---

## ✅ 업로드 확인

1. GitHub 레포지토리 페이지 새로고침
2. 파일들이 보이는지 확인
3. 코드가 정상적으로 업로드되었는지 확인

---

## 🔄 이후 업데이트 방법

**코드 수정 후 다시 업로드:**
```bash
# 1. 변경된 파일 추가
git add .

# 2. 커밋 생성
git commit -m "변경 내용 설명"

# 3. GitHub에 푸시
git push
```

---

## 📁 .gitignore 파일 확인

**`.gitignore` 파일이 있는지 확인:**
- `node_modules/` 제외
- `__pycache__/` 제외
- `.env` 제외 (환경 변수 파일)
- 기타 불필요한 파일 제외

**없으면 생성:**
```bash
# .gitignore 파일 생성
echo "node_modules/" > .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore
echo ".venv/" >> .gitignore
echo "dist/" >> .gitignore
echo "build/" >> .gitignore
```

---

## ⚠️ 문제 해결

### "fatal: remote origin already exists" 오류
```bash
git remote remove origin
git remote add origin https://github.com/culturecclllc/ktgktg.git
```

### "Permission denied" 오류
- Personal Access Token 확인
- GitHub 계정 권한 확인

### 큰 파일 업로드 오류
- Git LFS 설치 또는 `.gitignore`에 큰 파일 추가

---

**🎉 완료! 이제 Vercel과 Fly.io에서 이 레포지토리를 연결하여 배포할 수 있습니다!**
