from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import sys
import os
import jwt
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 현재 디렉토리의 notion 모듈 import
from notion.auth import check_login, save_article_to_notion, save_usage_log_to_notion, get_user_articles, get_user_api_keys_from_notion, save_user_api_keys_to_notion
from notion.article_db import save_article_to_notion_db, get_user_articles_from_notion_db
from llm_service import generate_title, generate_content, generate_draft, analyze_draft, generate_final

app = FastAPI(title="YNK 블로그 자동화")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ktgktg.vercel.app",  # Vercel 프론트엔드 URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ynk-blog-automation-secret-key-change-in-production")  # 프로덕션에서는 환경 변수로 설정
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7일

# 참고: API 키는 이제 Notion Database에 저장됩니다 (user_api_keys 딕셔너리는 사용하지 않음)


class LoginRequest(BaseModel):
    user_id: str
    user_pw: str


class GenerateTitleRequest(BaseModel):
    keyword: str
    model: str  # 'openai', 'groq', 'gemini'


class GenerateContentRequest(BaseModel):
    title: str
    keyword: Optional[str] = ""
    model: str  # 'openai', 'groq', 'gemini'


class GenerateDraftRequest(BaseModel):
    topic: str
    article_intent: str
    target_audience: str
    tone_style: str
    detailed_keywords: Optional[str] = ""
    age_groups: Optional[list] = []
    gender: Optional[str] = "전체"
    model: str  # 'openai', 'groq', 'gemini'
    api_key: Optional[str] = ""


class AnalyzeDraftRequest(BaseModel):
    draft_content: str
    model: str  # 'openai', 'groq', 'gemini'
    api_key: Optional[str] = ""


class GenerateFinalRequest(BaseModel):
    topic: str
    article_intent: str
    target_audience: str
    tone_style: str
    drafts: list[dict]
    analyses: list[dict]
    api_key: Optional[str] = ""
    model: Optional[str] = "gemini"  # 기본값은 gemini
    save_to_notion: Optional[bool] = False  # Notion에 저장할지 여부


class SaveArticleRequest(BaseModel):
    topic: str
    content: str
    article_intent: str
    target_audience: str
    model: str
    database_id: Optional[str] = None  # Notion Database ID (선택사항)


class JWTAuth:
    @staticmethod
    def create_token(user_id: str) -> str:
        """JWT 토큰 생성"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """JWT 토큰 검증 및 user_id 반환"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("user_id")
            return user_id
        except jwt.ExpiredSignatureError:
            # 토큰 만료
            return None
        except jwt.InvalidTokenError:
            # 토큰 무효
            return None


def get_jwt_token(request: Request) -> Optional[str]:
    """헤더나 쿠키에서 JWT 토큰 가져오기 (X-Session-ID 헤더 우선)"""
    token = request.headers.get("X-Session-ID")  # X-Session-ID 헤더에서 토큰 가져오기
    if not token:
        token = request.cookies.get("session_id")  # 없으면 쿠키에서 확인 (fallback)
    return token


def require_auth(request: Request):
    """인증이 필요한 엔드포인트용 의존성 (JWT 토큰 기반)"""
    token = get_jwt_token(request)
    
    # 디버깅 로그
    print(f"🔍 인증 확인: token={'있음' if token else '없음'}, X-Session-ID={request.headers.get('X-Session-ID', '없음')[:30]}...")
    
    if not token:
        print(f"❌ 토큰 없음: 로그인이 필요합니다.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다."
        )
    
    # JWT 토큰 검증
    user_id = JWTAuth.verify_token(token)
    
    if not user_id:
        print(f"❌ 토큰 만료 또는 무효: 토큰이 만료되었거나 유효하지 않습니다.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="세션이 만료되었습니다. 다시 로그인해주세요."
        )
    
    print(f"✅ 인증 성공: user_id={user_id}")
    return user_id


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """노션 기반 로그인"""
    try:
        if check_login(request.user_id, request.user_pw):
            # JWT 토큰 생성 (7일 유효)
            token = JWTAuth.create_token(request.user_id)
            print(f"✅ 로그인 성공: user_id={request.user_id}, JWT 토큰 생성됨 (7일 유효)")
            
            response = JSONResponse({
                "success": True,
                "message": "로그인 성공",
                "session_id": token  # JWT 토큰을 session_id로 반환 (프론트엔드 호환성 유지)
            })
            response.set_cookie(
                key="session_id",
                value=token,
                httponly=True,
                samesite="none",  # 다른 도메인 간 요청을 위해 "none" 필요
                secure=True,  # HTTPS 환경을 위해 필요
                max_age=JWT_EXPIRATION_HOURS * 3600,  # 7일 (초 단위)
                domain=None  # 도메인을 명시하지 않으면 요청 도메인에 자동 설정
            )
            return response
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="아이디 또는 비밀번호가 틀립니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 처리 중 오류: {str(e)}"
        )


@app.post("/api/auth/logout")
async def logout(request: Request):
    """로그아웃"""
    session_id = get_session_id(request)
    if session_id:
        SessionManager.delete_session(session_id)
    return {"success": True, "message": "로그아웃 완료"}


@app.get("/api/auth/check")
async def check_auth(user_id: str = Depends(require_auth)):
    """인증 상태 확인"""
    return {"authenticated": True, "user_id": user_id}


@app.post("/api/generate/title")
async def generate_title_endpoint(
    request: GenerateTitleRequest,
    user_id: str = Depends(require_auth)
):
    """제목 생성"""
    try:
        title = generate_title(request.keyword, request.model)
        return {"title": title}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제목 생성 중 오류: {str(e)}"
        )


@app.post("/api/generate/content")
async def generate_content_endpoint(
    request: GenerateContentRequest,
    user_id: str = Depends(require_auth)
):
    """본문 생성"""
    try:
        content = generate_content(request.title, request.keyword, request.model)
        return {"content": content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"본문 생성 중 오류: {str(e)}"
        )


@app.post("/api/generate/draft")
async def generate_draft_endpoint(
    request: GenerateDraftRequest,
    user_id: str = Depends(require_auth)
):
    """초안 생성 (주제 기반)"""
    try:
        print(f"📝 초안 생성 요청: user_id={user_id}, model={request.model}, topic={request.topic[:50]}...")
        
        # API 키 가져오기 (사용자별 저장된 키 또는 요청에서 제공된 키)
        api_key = request.api_key
        if not api_key:
            # Notion Database에서 사용자별 저장된 API 키 확인
            user_keys = get_user_api_keys_from_notion(user_id)
            if request.model == 'openai':
                api_key = user_keys.get('openai', '')
            elif request.model == 'groq':
                api_key = user_keys.get('groq', '')
            elif request.model == 'gemini':
                api_key = user_keys.get('gemini', '')
        
        if api_key:
            print(f"   {request.model.upper()} API 키 사용: {api_key[:10]}...")
        
        content = generate_draft(
            request.topic,
            request.article_intent,
            request.target_audience,
            request.tone_style,
            request.model,
            request.detailed_keywords or "",
            request.age_groups or [],
            request.gender or "전체",
            api_key=api_key  # API 키 직접 전달
        )
        
        print(f"✅ 초안 생성 성공: user_id={user_id}, model={request.model}, content_length={len(content)}")
        
        # 초안을 Notion 기록용 Database에 저장 (백그라운드, 실패해도 계속 진행)
        try:
            success = save_article_to_notion_db(
                user_id=user_id,
                topic=request.topic,
                content=content,
                article_intent=request.article_intent,
                target_audience=request.target_audience,
                model=request.model,
                article_type="초안"
            )
            if success:
                print(f"✅ 초안 Notion 저장 성공: {user_id} - {request.topic}")
            else:
                print(f"❌ 초안 Notion 저장 실패: {user_id} - {request.topic}")
        except Exception as e:
            print(f"❌ 초안 Notion 저장 중 예외 발생: {user_id} - {request.topic}")
            print(f"   에러 상세: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 사용 기록 저장은 별도 Database가 필요하므로 일단 비활성화
        # 필요시 별도 Database를 설정하고 활성화하세요
        # try:
        #     save_usage_log_to_notion(
        #         user_id=user_id,
        #         action_type="초안생성",
        #         model=request.model,
        #         topic=request.topic
        #     )
        # except Exception as e:
        #     print(f"사용 기록 저장 실패 (무시): {e}")
        
        return {"content": content}
    except HTTPException:
        # HTTPException은 그대로 전달
        raise
    except Exception as e:
        error_msg = str(e)
        error_dict = {}
        
        # 디버깅 로그
        print(f"❌ 초안 생성 실패: user_id={user_id}, model={request.model}, error={error_msg}")
        import traceback
        traceback.print_exc()
        
        # 에러 메시지에서 딕셔너리 추출 시도
        import json
        import re
        import ast
        # Python 딕셔너리 문자열 찾기 (예: "Error code: 429 - {'error': {...}}")
        dict_match = re.search(r"Error code: \d+ - (\{.*\})", error_msg, re.DOTALL)
        if dict_match:
            try:
                error_dict = ast.literal_eval(dict_match.group(1))
            except:
                try:
                    # JSON 형식으로 시도
                    dict_str = dict_match.group(1).replace("'", '"')
                    error_dict = json.loads(dict_str)
                except:
                    pass
        
        # OpenAI 할당량 초과 에러 처리 (OpenAI 모델일 때만)
        error_code = error_dict.get('error', {}).get('code', '')
        error_type = error_dict.get('error', {}).get('type', '')
        
        # 모델 타입에 따라 다른 에러 메시지 표시
        model_type = getattr(request, 'model', 'unknown')
        
        if model_type == 'openai':
            if ("insufficient_quota" in error_msg or "quota" in error_msg.lower() or 
                error_code == 'insufficient_quota' or error_type == 'insufficient_quota'):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="OpenAI API 할당량이 초과되었습니다. 계정의 결제 정보와 사용량을 확인해주세요. https://platform.openai.com/usage"
                )
        elif model_type == 'gemini':
            if ("quota" in error_msg.lower() or "429" in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Gemini API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요. https://ai.google.dev/pricing"
                )
            elif ("invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "API key" in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Gemini API 키가 유효하지 않습니다. API 키를 확인해주세요. https://ai.google.dev/"
                )
        elif model_type == 'groq':
            if ("model_decommissioned" in error_msg or "decommissioned" in error_msg.lower() or
                error_code == 'model_decommissioned' or "llama-3.1-70b-versatile" in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="사용 중인 Groq 모델(llama-3.1-70b-versatile)이 더 이상 지원되지 않습니다. llama-3.3-70b-versatile 모델로 업데이트되었습니다. https://console.groq.com/docs/deprecations"
                )
            elif ("quota" in error_msg.lower() or "429" in error_msg):
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Groq API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요. https://console.groq.com/limits"
                )
            elif ("invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Groq API 키가 유효하지 않습니다. API 키를 확인해주세요. https://console.groq.com/keys"
                )
        
        # ValueError는 그대로 전달 (API 키 오류 등)
        if isinstance(e, ValueError):
            # API 키 관련 오류인지 확인
            if "API_KEY" in error_msg or "API key" in error_msg or "환경변수" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{model_type.upper()} API 키가 설정되지 않았습니다. 설정 페이지에서 API 키를 입력해주세요."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"초안 생성 중 오류: {error_msg}"
                )
        
        # 에러 메시지에서 핵심 정보 추출
        if error_dict.get('error', {}).get('message'):
            clean_msg = error_dict['error']['message']
        else:
            clean_msg = error_msg
        
        # 일반적인 서버 오류
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"초안 생성 중 오류: {clean_msg}"
        )


@app.post("/api/analyze/draft")
async def analyze_draft_endpoint(
    request: AnalyzeDraftRequest,
    user_id: str = Depends(require_auth)
):
    """초안 장단점 분석"""
    try:
        # API 키 가져오기 (사용자별 저장된 키 또는 요청에서 제공된 키)
        api_key = request.api_key
        if not api_key:
            # Notion Database에서 사용자별 저장된 API 키 확인
            user_keys = get_user_api_keys_from_notion(user_id)
            if request.model == 'openai':
                api_key = user_keys.get('openai', '')
            elif request.model == 'groq':
                api_key = user_keys.get('groq', '')
            elif request.model == 'gemini':
                api_key = user_keys.get('gemini', '')
        
        if api_key:
            print(f"   {request.model.upper()} API 키 사용: {api_key[:10]}...")
        
        result = analyze_draft(request.draft_content, request.model, api_key=api_key)
        
        # 사용 기록 저장은 별도 Database가 필요하므로 일단 비활성화
        # 필요시 별도 Database를 설정하고 활성화하세요
        # try:
        #     save_usage_log_to_notion(
        #         user_id=user_id,
        #         action_type="장단점분석",
        #         model=request.model,
        #         topic="분석 완료"
        #     )
        # except Exception as e:
        #     print(f"사용 기록 저장 실패 (무시): {e}")
        
        return result
    except Exception as e:
        error_msg = str(e)
        error_dict = {}
        
        # 에러 메시지에서 딕셔너리 추출 시도
        import json
        import re
        import ast
        # Python 딕셔너리 문자열 찾기 (예: "Error code: 429 - {'error': {...}}")
        dict_match = re.search(r"Error code: \d+ - (\{.*\})", error_msg, re.DOTALL)
        if dict_match:
            try:
                error_dict = ast.literal_eval(dict_match.group(1))
            except:
                try:
                    # JSON 형식으로 시도
                    dict_str = dict_match.group(1).replace("'", '"')
                    error_dict = json.loads(dict_str)
                except:
                    pass
        
        # OpenAI 할당량 초과 에러 처리
        error_code = error_dict.get('error', {}).get('code', '')
        error_type = error_dict.get('error', {}).get('type', '')
        
        if ("insufficient_quota" in error_msg or "quota" in error_msg.lower() or 
            error_code == 'insufficient_quota' or error_type == 'insufficient_quota'):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="OpenAI API 할당량이 초과되었습니다. 계정의 결제 정보와 사용량을 확인해주세요. https://platform.openai.com/usage"
            )
        # Groq 모델 에러 처리
        if ("model_decommissioned" in error_msg or "decommissioned" in error_msg.lower() or
            error_code == 'model_decommissioned' or "llama-3.1-70b-versatile" in error_msg):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용 중인 Groq 모델(llama-3.1-70b-versatile)이 더 이상 지원되지 않습니다. llama-3.3-70b-versatile 모델로 업데이트되었습니다. https://console.groq.com/docs/deprecations"
            )
        # 에러 메시지에서 핵심 정보 추출
        if error_dict.get('error', {}).get('message'):
            clean_msg = error_dict['error']['message']
        else:
            clean_msg = error_msg
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"장단점 분석 중 오류: {clean_msg}"
        )


@app.post("/api/generate/final")
async def generate_final_endpoint(
    request: GenerateFinalRequest,
    user_id: str = Depends(require_auth)
):
    """최종 고품질 글 생성 (3개 모델 강점 조합)"""
    try:
        print(f"📝 최종 글 생성 요청: user_id={user_id}, model={request.model or 'gemini'}")
        
        # API 키 가져오기 (사용자별 저장된 키 또는 요청에서 제공된 키)
        model = request.model or 'gemini'
        api_key = request.api_key
        if not api_key:
            # 사용자별 저장된 API 키 확인
            user_keys = user_api_keys.get(user_id, {})
            if model == 'gemini':
                api_key = user_keys.get('gemini', '')
            elif model == 'openai':
                api_key = user_keys.get('openai', '')
            elif model == 'groq':
                api_key = user_keys.get('groq', '')
        
        if api_key:
            print(f"   {model.upper()} API 키 사용: {api_key[:10]}...")
        
        content = generate_final(
            request.topic,
            request.article_intent,
            request.target_audience,
            request.tone_style,
            request.drafts,
            request.analyses,
            api_key=api_key  # API 키 직접 전달
        )
        
        print(f"✅ 최종 글 생성 성공: user_id={user_id}, content_length={len(content)}")
        
        # 최종 글을 Notion 기록용 Database에 자동 저장 (백그라운드, 실패해도 계속 진행)
        try:
            success = save_article_to_notion_db(
                user_id=user_id,
                topic=request.topic,
                content=content,
                article_intent=request.article_intent,
                target_audience=request.target_audience,
                model=request.model or "gemini",
                article_type="최종글"
            )
            if success:
                print(f"✅ 최종 글 Notion 저장 성공: {user_id} - {request.topic}")
            else:
                print(f"❌ 최종 글 Notion 저장 실패: {user_id} - {request.topic}")
        except Exception as e:
            print(f"❌ 최종 글 Notion 저장 중 예외 발생: {user_id} - {request.topic}")
            print(f"   에러 상세: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 사용 기록 저장은 별도 Database가 필요하므로 일단 비활성화
        # 필요시 별도 Database를 설정하고 활성화하세요
        # try:
        #     save_usage_log_to_notion(
        #         user_id=user_id,
        #         action_type="최종글생성",
        #         model=request.model or "gemini",
        #         topic=request.topic
        #     )
        # except Exception as e:
        #     print(f"사용 기록 저장 실패 (무시): {e}")
        
        return {"content": content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"최종 생성 중 오류: {str(e)}"
        )


@app.post("/api/save/article")
async def save_article_endpoint(
    request: SaveArticleRequest,
    user_id: str = Depends(require_auth)
):
    """생성된 글을 Notion에 저장"""
    try:
        success = save_article_to_notion(
            user_id=user_id,
            topic=request.topic,
            content=request.content,
            article_intent=request.article_intent,
            target_audience=request.target_audience,
            model=request.model,
            database_id=request.database_id
        )
        if success:
            return {"success": True, "message": "Notion에 저장되었습니다."}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Notion 저장에 실패했습니다."
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장 중 오류: {str(e)}"
        )


@app.get("/api/history/articles")
async def get_user_articles_endpoint(
    user_id: str = Depends(require_auth),
    database_id: Optional[str] = None
):
    """사용자가 생성한 글 목록 조회 (기록용 Database)"""
    try:
        # 기록용 Database에서 조회
        articles = get_user_articles_from_notion_db(user_id, database_id)
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기록 조회 중 오류: {str(e)}"
        )


class ApiKeysRequest(BaseModel):
    openai: Optional[str] = ""
    groq: Optional[str] = ""
    gemini: Optional[str] = ""


@app.post("/api/settings/api-keys")
async def save_api_keys(
    request: ApiKeysRequest,
    user_id: str = Depends(require_auth)
):
    """사용자별 API 키 저장 (Notion Database에 저장)"""
    try:
        # user_id 검증
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자 인증 정보가 유효하지 않습니다."
            )
        
        user_id = user_id.strip()
        
        # Notion Database에 저장 (빈 문자열이 아닌 경우만 업데이트, 빈 문자열이면 기존 값 유지)
        openai_key = request.openai.strip() if (request.openai and request.openai.strip()) else ""
        groq_key = request.groq.strip() if (request.groq and request.groq.strip()) else ""
        gemini_key = request.gemini.strip() if (request.gemini and request.gemini.strip()) else ""
        
        # Notion Database에 저장 (save_user_api_keys_to_notion이 빈 문자열 처리)
        success = save_user_api_keys_to_notion(
            user_id=user_id,
            openai_key=openai_key,
            groq_key=groq_key,
            gemini_key=gemini_key
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Notion Database에 API 키 저장에 실패했습니다."
            )
        
        # 저장 후 최종 값 조회 (로그용)
        final_keys = get_user_api_keys_from_notion(user_id)
        
        # 디버깅 로그
        print(f"✅ API 키 저장 완료 (Notion): user_id='{user_id}', openai={'설정됨' if final_keys.get('openai') else '없음'}, groq={'설정됨' if final_keys.get('groq') else '없음'}, gemini={'설정됨' if final_keys.get('gemini') else '없음'}")
        
        return {"success": True, "message": "API 키가 저장되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API 키 저장 실패: user_id='{user_id}', error={str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 키 저장 중 오류: {str(e)}"
        )


@app.get("/api/settings/api-keys")
async def get_api_keys(
    user_id: str = Depends(require_auth)
):
    """사용자별 API 키 조회 (Notion Database에서 조회)"""
    try:
        # user_id 검증
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자 인증 정보가 유효하지 않습니다."
            )
        
        user_id = user_id.strip()
        
        # Notion Database에서 조회
        api_keys = get_user_api_keys_from_notion(user_id)
        
        # 디버깅 로그
        print(f"🔍 API 키 조회 (Notion): user_id='{user_id}', openai={'설정됨' if api_keys.get('openai') else '없음'}, groq={'설정됨' if api_keys.get('groq') else '없음'}, gemini={'설정됨' if api_keys.get('gemini') else '없음'}")
        
        return {"api_keys": api_keys}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ API 키 조회 실패: user_id='{user_id}', error={str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 키 조회 중 오류: {str(e)}"
        )


@app.get("/")
async def root():
    return {"message": "YNK 블로그 자동화 API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
