# GitHub API 키 제거 및 환경 변수 설정 가이드

## ✅ 완료된 작업

1. ✅ `backend/notion/auth.py` - API 키를 환경 변수로 변경
2. ✅ `backend/notion/article_db.py` - API 키를 환경 변수로 변경
3. ✅ `backend/env.example` - 환경 변수 템플릿 파일 생성

## 🔄 다음 단계: 커밋 수정 및 다시 푸시

### 1. 변경된 파일 추가
```bash
cd "C:\Users\OoOoO\서이추\멀티 자동화"
git add backend/notion/auth.py backend/notion/article_db.py backend/env.example
```

### 2. 마지막 커밋 수정 (API 키 제거)
```bash
git commit --amend --no-edit
```

이 명령어는 마지막 커밋에 현재 변경사항을 추가합니다.

### 3. GitHub에 강제 푸시
```bash
git push -f origin main
```

⚠️ **주의**: `-f` (force) 옵션은 강제 푸시입니다. 이미 푸시한 내용을 덮어씁니다.

---

## 📝 환경 변수 설정 방법

### 로컬 개발 시

`backend` 폴더에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Notion API Keys
NOTION_API_KEY=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
NOTION_DATABASE_ID=2e4be3c7b2548070b4dcf2e06e9e7baf

# 글 저장용 Notion API 키
ARTICLE_NOTION_API_KEY=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
ARTICLE_DATABASE_ID=2eabe3c7b25480a5b8e2fbb68b891e77
```

### Python에서 환경 변수 읽기

코드에서 `python-dotenv`를 사용하려면:

1. `requirements.txt`에 추가:
```
python-dotenv>=1.0.0
```

2. `main.py` 상단에 추가:
```python
from dotenv import load_dotenv
load_dotenv()  # .env 파일에서 환경 변수 로드
```

---

## 🚀 배포 시 환경 변수 설정

### Vercel (프론트엔드)
- Vercel 대시보드 → Settings → Environment Variables
- `NEXT_PUBLIC_BACKEND_URL` 추가

### Fly.io (백엔드)
```bash
cd backend
fly secrets set NOTION_API_KEY="ntn_..." NOTION_DATABASE_ID="2e4..." ARTICLE_NOTION_API_KEY="ntn_..." ARTICLE_DATABASE_ID="2eab..."
```

---

## ✅ 확인

푸시 후 GitHub 레포지토리에서:
1. `backend/notion/auth.py` - API 키가 하드코딩되어 있지 않은지 확인
2. `backend/notion/article_db.py` - API 키가 하드코딩되어 있지 않은지 확인
3. GitHub Secret Scanning 경고가 사라졌는지 확인
