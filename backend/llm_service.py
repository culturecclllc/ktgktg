"""
Multi-LLM 서비스 통합
OpenAI GPT-5 Nano, Groq (Llama), Gemini 2.5 Flash-Lite 지원
"""
import os
import json
import re
import ast
from typing import Optional

# OpenAI 에러 타입
try:
    from openai import APIError, RateLimitError, APIConnectionError, AuthenticationError
    OPENAI_ERROR_TYPES_AVAILABLE = True
except ImportError:
    OPENAI_ERROR_TYPES_AVAILABLE = False

# Groq 에러 타입
try:
    from groq import APIError as GroqAPIError, RateLimitError as GroqRateLimitError
    GROQ_ERROR_TYPES_AVAILABLE = True
except ImportError:
    GROQ_ERROR_TYPES_AVAILABLE = False


def parse_error_dict(error_str: str) -> dict:
    """에러 문자열에서 딕셔너리 추출"""
    error_dict = {}
    
    # Python 딕셔너리 문자열 찾기 (예: "{'error': {'message': '...', 'code': '...'}}")
    dict_patterns = [
        r"\{'error':\s*\{[^}]+\}\}",  # {'error': {...}}
        r'\{"error":\s*\{[^}]+\}\}',  # {"error": {...}}
        r"Error code: \d+ - (\{.*\})",  # Error code: 429 - {...}
    ]
    
    for pattern in dict_patterns:
        match = re.search(pattern, error_str, re.DOTALL)
        if match:
            try:
                dict_str = match.group(1) if match.groups() else match.group()
                # Python 딕셔너리 문자열을 실제 딕셔너리로 변환
                error_dict = ast.literal_eval(dict_str)
                break
            except:
                try:
                    # JSON 형식으로 시도
                    dict_str = dict_str.replace("'", '"')
                    error_dict = json.loads(dict_str)
                    break
                except:
                    continue
    
    return error_dict

# OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Groq (Llama 모델)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def get_openai_client():
    """OpenAI 클라이언트 생성"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


def get_groq_client():
    """Groq 클라이언트 생성"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY 환경변수가 설정되지 않았습니다.")
    return Groq(api_key=api_key)


def get_gemini_client():
    """Gemini 클라이언트 생성"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-lite')


def generate_title(keyword: str, model_type: str = "openai") -> str:
    """
    키워드로부터 블로그 제목 생성
    
    Args:
        keyword: 블로그 키워드
        model_type: 'openai', 'groq', 'gemini'
    
    Returns:
        생성된 제목
    """
    prompt = f"""다음 키워드를 기반으로 SEO 최적화된 블로그 제목을 1개만 생성해주세요.

키워드: {keyword}

요구사항:
1. 제목은 30-50자 정도로 작성
2. 클릭을 유도하는 매력적인 제목
3. 키워드를 자연스럽게 포함
4. 숫자나 질문형 제목 권장
5. 한국어로만 작성

제목만 출력하세요 (설명 없이):"""

    if model_type == "openai":
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI 라이브러리가 설치되지 않았습니다. pip install openai")
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # GPT-5 Nano는 아직 없으므로 최신 모델 사용
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e)
            error_dict = parse_error_dict(error_str)
            
            # OpenAI APIError 객체에서 에러 정보 추출
            if OPENAI_ERROR_TYPES_AVAILABLE and isinstance(e, APIError):
                if hasattr(e, 'response') and e.response:
                    try:
                        error_dict = e.response.json() if hasattr(e.response, 'json') else {}
                    except:
                        pass
                if hasattr(e, 'body'):
                    try:
                        if isinstance(e.body, dict):
                            error_dict = e.body
                        elif isinstance(e.body, str):
                            error_dict = json.loads(e.body)
                    except:
                        pass
            
            # 에러 메시지에서 정보 추출
            error_code = error_dict.get('error', {}).get('code', '')
            error_type = error_dict.get('error', {}).get('type', '')
            
            if ("insufficient_quota" in error_str or "quota" in error_str.lower() or 
                error_code == 'insufficient_quota' or error_type == 'insufficient_quota'):
                raise ValueError("OpenAI API 할당량이 초과되었습니다. 계정의 결제 정보와 사용량을 확인해주세요. https://platform.openai.com/usage")
            elif ("rate_limit" in error_str.lower() or "429" in error_str or 
                  (OPENAI_ERROR_TYPES_AVAILABLE and isinstance(e, RateLimitError))):
                raise ValueError("OpenAI API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif ("invalid_api_key" in error_str.lower() or "authentication" in error_str.lower() or
                  (OPENAI_ERROR_TYPES_AVAILABLE and isinstance(e, AuthenticationError))):
                raise ValueError("OpenAI API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                # 원본 에러 메시지에서 핵심 정보만 추출
                if error_dict.get('error', {}).get('message'):
                    raise ValueError(f"OpenAI API 오류: {error_dict['error']['message']}")
                else:
                    raise ValueError(f"OpenAI API 오류: {error_str}")
    
    elif model_type == "groq":
        if not GROQ_AVAILABLE:
            raise ValueError("Groq 라이브러리가 설치되지 않았습니다. pip install groq")
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Groq의 최신 Llama 모델 (llama-3.1-70b-versatile은 2025-01-24 폐기됨)
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e)
            error_dict = parse_error_dict(error_str)
            
            # Groq APIError 객체에서 에러 정보 추출
            if GROQ_ERROR_TYPES_AVAILABLE and isinstance(e, GroqAPIError):
                if hasattr(e, 'response') and e.response:
                    try:
                        error_dict = e.response.json() if hasattr(e.response, 'json') else {}
                    except:
                        pass
                if hasattr(e, 'body'):
                    try:
                        if isinstance(e.body, dict):
                            error_dict = e.body
                        elif isinstance(e.body, str):
                            error_dict = json.loads(e.body)
                    except:
                        pass
            
            # 에러 메시지에서 정보 추출
            error_code = error_dict.get('error', {}).get('code', '')
            error_type = error_dict.get('error', {}).get('type', '')
            
            if ("model_decommissioned" in error_str or "decommissioned" in error_str.lower() or
                error_code == 'model_decommissioned' or "llama-3.1-70b-versatile" in error_str):
                raise ValueError("사용 중인 Groq 모델(llama-3.1-70b-versatile)이 더 이상 지원되지 않습니다. llama-3.3-70b-versatile 모델로 업데이트되었습니다. https://console.groq.com/docs/deprecations")
            elif ("rate_limit" in error_str.lower() or "429" in error_str or
                  (GROQ_ERROR_TYPES_AVAILABLE and isinstance(e, GroqRateLimitError))):
                raise ValueError("Groq API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif ("invalid_api_key" in error_str.lower() or "authentication" in error_str.lower()):
                raise ValueError("Groq API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                # 원본 에러 메시지에서 핵심 정보만 추출
                if error_dict.get('error', {}).get('message'):
                    raise ValueError(f"Groq API 오류: {error_dict['error']['message']}")
                else:
                    raise ValueError(f"Groq API 오류: {error_str}")
    
    elif model_type == "gemini":
        if not GEMINI_AVAILABLE:
            raise ValueError("Google Generative AI 라이브러리가 설치되지 않았습니다. pip install google-generativeai")
        model = get_gemini_client()
        response = model.generate_content(prompt)
        return response.text.strip()
    
    else:
        raise ValueError(f"지원하지 않는 모델 타입: {model_type}")


def generate_content(title: str, keyword: str = "", model_type: str = "openai") -> str:
    """
    제목으로부터 블로그 본문 생성
    
    Args:
        title: 블로그 제목
        keyword: 관련 키워드 (선택)
        model_type: 'openai', 'groq', 'gemini'
    
    Returns:
        생성된 본문
    """
    prompt = f"""다음 제목을 기반으로 SEO 최적화된 블로그 본문을 작성해주세요.

제목: {title}
{f'키워드: {keyword}' if keyword else ''}

중요 지시사항:
1. 반드시 한국어(한글)로만 작성하세요. 한자, 아랍어, 기타 외국어는 절대 사용하지 마세요.
2. 한국어 맞춤법과 띄어쓰기 규칙을 정확히 따르세요.
3. 이모티콘이나 특수문자 사용 금지
4. 정보 제공 중심의 마케팅 톤 사용 (과장 없이 사실 기반)
5. "~입니다", "~합니다" 존댓말 사용
6. 간결하고 읽기 쉬운 문장으로 작성해주세요

요구사항:
1. 서론: 질문이나 상황 제시로 시작하여 독자의 관심을 끌기 (2-3문단)
2. 본론: 구체적인 내용을 소제목(##)으로 나누어 설명 (5-7개 소제목)
   - 각 소제목은 명확한 주제 제시
   - 각 소제목 아래 2-3개 문단으로 설명
   - 구체적인 숫자와 예시 반드시 포함
3. 결론: 타겟 고객층을 명시하고 마무리 (2-3문단)
4. 제목의 핵심 키워드를 자연스럽게 본문에 3-5회 포함해주세요.
5. 전체 글자 수는 1500-2500자 정도로 작성해주세요.

다음 형식으로 작성해주세요:
[서론]

질문이나 상황 제시...

[본론]

## 소제목1

첫 번째 문단 설명...

두 번째 문단 설명...

## 소제목2

첫 번째 문단 설명...

[결론]

타겟 고객층 명시...

마무리 문단..."""

    if model_type == "openai":
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI 라이브러리가 설치되지 않았습니다. pip install openai")
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=4000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e)
            if "insufficient_quota" in error_str or "quota" in error_str.lower():
                raise ValueError("OpenAI API 할당량이 초과되었습니다. 계정의 결제 정보와 사용량을 확인해주세요. https://platform.openai.com/usage")
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                raise ValueError("OpenAI API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                raise ValueError("OpenAI API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"OpenAI API 오류: {error_str}")
    
    elif model_type == "groq":
        if not GROQ_AVAILABLE:
            raise ValueError("Groq 라이브러리가 설치되지 않았습니다. pip install groq")
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=4000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e)
            if "model_decommissioned" in error_str or "decommissioned" in error_str.lower():
                raise ValueError("사용 중인 Groq 모델이 더 이상 지원되지 않습니다. llama-3.3-70b-versatile 모델을 사용해주세요. https://console.groq.com/docs/deprecations")
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                raise ValueError("Groq API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                raise ValueError("Groq API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"Groq API 오류: {error_str}")
    
    elif model_type == "gemini":
        if not GEMINI_AVAILABLE:
            raise ValueError("Google Generative AI 라이브러리가 설치되지 않았습니다. pip install google-generativeai")
        model = get_gemini_client()
        response = model.generate_content(prompt)
        return response.text.strip()
    
    else:
        raise ValueError(f"지원하지 않는 모델 타입: {model_type}")


def generate_draft(topic: str, article_intent: str, target_audience: str, tone_style: str, model_type: str = "openai", detailed_keywords: str = "", age_groups: list = None, gender: str = "전체") -> str:
    """
    주제 기반으로 블로그 초안 생성
    
    Args:
        topic: 블로그 주제
        article_intent: 글 의도 ('정보성', '튜토리얼', '비교/리뷰')
        target_audience: 대상 독자
        tone_style: 톤/스타일
        model_type: 'openai', 'groq', 'gemini'
    
    Returns:
        생성된 초안
    """
    keywords_text = f"\n세부 키워드: {detailed_keywords}" if detailed_keywords else ""
    age_text = f"\n연령층: {', '.join(age_groups) if age_groups else '전체'}"
    gender_text = f"\n성별: {gender}"
    
    prompt = f"""다음 정보를 바탕으로 블로그 글 초안을 작성해주세요.

주제: {topic}
글 의도: {article_intent}
대상 독자: {target_audience}
톤/스타일: {tone_style}{keywords_text}{age_text}{gender_text}

요구사항:
1. 주제에 맞는 구체적이고 실용적인 내용 작성
2. 대상 독자에게 맞는 수준과 톤으로 작성
3. 글 의도에 맞는 구조로 작성
   - 정보성: 정보 제공 중심, 객관적 사실 나열
   - 튜토리얼: 단계별 가이드 형식
   - 비교/리뷰: 비교 분석과 평가 중심
   - 방문후기/여행기: 경험 중심의 생생한 묘사
   - 제품 리뷰/홍보: 제품 특징과 사용 후기
   - 문제 해결 가이드: 문제-원인-해결책 구조
   - 교육/강의: 체계적인 학습 내용 전달
   - 스토리텔링: 이야기 형식의 흥미로운 구성
   - 브랜딩: 브랜드 가치와 정체성 강조
   - 설득/마케팅: 설득력 있는 논리와 감성적 어필
   - 엔터테인먼트: 재미있고 흥미로운 내용
   - 맛집: 음식과 맛에 대한 상세한 묘사
   - 일상생각: 개인적 경험과 생각 공유
   - 상품리뷰: 상품의 장단점과 추천 여부
   - 경제비즈니스: 경제 동향과 비즈니스 인사이트
   - IT컴퓨터: 기술적 내용과 사용법
   - 교육학문: 학술적 내용과 지식 전달
4. 톤/스타일을 일관되게 유지
5. **절대적으로 한국어로만 작성**
   - 한자(漢字, 积累 등) 사용 절대 금지
   - 일본어(まず, です 등) 사용 절대 금지
   - 중국어 사용 절대 금지
   - 영어는 최소한으로만 사용 (필수 전문용어만)
   - 모든 내용은 한글로만 작성
   - 숫자는 아라비아 숫자 사용 가능 (1, 2, 3 등)
6. 1500-2500자 정도로 충실하게 작성
7. **중요: 마크다운 형식 사용 금지**
   - **볼드(**텍스트**)**, *이탤릭*, ### 헤딩 등 텍스트 스타일링 마크다운 사용 금지
   - 해시태그(#컬쳐캐피탈)는 예외로 사용 가능
   - 일반 텍스트로만 작성 (줄바꿈은 엔터로 구분)

초안:"""

    if model_type == "openai":
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI 라이브러리가 설치되지 않았습니다. pip install openai")
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            content = response.choices[0].message.content.strip()
            
            # 마크다운 스타일링 제거 (해시태그는 유지)
            import re
            # **볼드** 제거
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            # *이탤릭* 제거
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            # ### 헤딩 제거 (해시태그는 유지하기 위해 공백 뒤에 오는 경우만)
            content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
            
            # 한자/일본어/중국어/러시아어/베트남어 등 비한글 문자 제거
            # 한자 범위: \u4e00-\u9fff (CJK 통합 한자)
            # 히라가나: \u3040-\u309f
            # 가타카나: \u30a0-\u30ff
            # 키릴 문자(러시아어): \u0400-\u04ff
            # 베트남어 확장: \u1e00-\u1eff
            # 태국어: \u0e00-\u0e7f
            # 아랍어: \u0600-\u06ff
            
            # 한자 제거
            content = re.sub(r'[\u4e00-\u9fff]+', '', content)
            # 일본어 히라가나/가타카나 제거
            content = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', '', content)
            # 러시아어 키릴 문자 제거
            content = re.sub(r'[\u0400-\u04ff]+', '', content)
            # 베트남어/태국어/아랍어 등 기타 문자 제거
            content = re.sub(r'[\u1e00-\u1eff\u0e00-\u0e7f\u0600-\u06ff]+', '', content)
            
            return content
        except Exception as e:
            error_str = str(e)
            if "insufficient_quota" in error_str or "quota" in error_str.lower():
                raise ValueError("OpenAI API 할당량이 초과되었습니다. 계정의 결제 정보와 사용량을 확인해주세요. https://platform.openai.com/usage")
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                raise ValueError("OpenAI API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                raise ValueError("OpenAI API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"OpenAI API 오류: {error_str}")
    
    elif model_type == "groq":
        if not GROQ_AVAILABLE:
            raise ValueError("Groq 라이브러리가 설치되지 않았습니다. pip install groq")
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            content = response.choices[0].message.content.strip()
            
            # 마크다운 스타일링 제거 (해시태그는 유지)
            import re
            # **볼드** 제거
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            # *이탤릭* 제거
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            # ### 헤딩 제거 (해시태그는 유지하기 위해 공백 뒤에 오는 경우만)
            content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
            
            # 한자/일본어/중국어/러시아어/베트남어 등 비한글 문자 제거
            # 한자 범위: \u4e00-\u9fff (CJK 통합 한자)
            # 히라가나: \u3040-\u309f
            # 가타카나: \u30a0-\u30ff
            # 키릴 문자(러시아어): \u0400-\u04ff
            # 베트남어 확장: \u1e00-\u1eff
            # 태국어: \u0e00-\u0e7f
            # 아랍어: \u0600-\u06ff
            
            # 한자 제거
            content = re.sub(r'[\u4e00-\u9fff]+', '', content)
            # 일본어 히라가나/가타카나 제거
            content = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', '', content)
            # 러시아어 키릴 문자 제거
            content = re.sub(r'[\u0400-\u04ff]+', '', content)
            # 베트남어/태국어/아랍어 등 기타 문자 제거
            content = re.sub(r'[\u1e00-\u1eff\u0e00-\u0e7f\u0600-\u06ff]+', '', content)
            
            return content
        except Exception as e:
            error_str = str(e)
            if "model_decommissioned" in error_str or "decommissioned" in error_str.lower():
                raise ValueError("사용 중인 Groq 모델이 더 이상 지원되지 않습니다. llama-3.3-70b-versatile 모델을 사용해주세요. https://console.groq.com/docs/deprecations")
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                raise ValueError("Groq API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                raise ValueError("Groq API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"Groq API 오류: {error_str}")
    
    elif model_type == "gemini":
        if not GEMINI_AVAILABLE:
            raise ValueError("Google Generative AI 라이브러리가 설치되지 않았습니다. pip install google-generativeai")
        try:
            model = get_gemini_client()
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # 마크다운 스타일링 제거 (해시태그는 유지)
            import re
            # **볼드** 제거
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            # *이탤릭* 제거
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            # ### 헤딩 제거 (해시태그는 유지하기 위해 공백 뒤에 오는 경우만)
            content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
            
            return content
        except Exception as e:
            error_str = str(e)
            if "quota" in error_str.lower() or "429" in error_str:
                raise ValueError("Gemini API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower() or "API key" in error_str:
                raise ValueError("Gemini API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"Gemini API 오류: {error_str}")
    
    else:
        raise ValueError(f"지원하지 않는 모델 타입: {model_type}")


def analyze_draft(draft_content: str, model_type: str = "openai") -> dict:
    """
    초안의 장단점 분석
    
    Args:
        draft_content: 분석할 초안 내용
        model_type: 'openai', 'groq', 'gemini'
    
    Returns:
        {'pros': [...], 'cons': [...], 'improvement': '...'}
    """
    prompt = f"""다음 블로그 글 초안을 분석하여 장점, 단점, 개선사항을 제시해주세요.

초안 내용:
{draft_content}

다음 형식으로 JSON 형태로 응답해주세요:
{{
  "pros": ["장점1", "장점2"],
  "cons": ["단점1", "단점2"],
  "improvement": "개선 방안을 한 문장으로 제시"
}}

요구사항:
1. 장점은 2-3개 정도로 구체적으로 제시
2. 단점은 1-2개 정도로 구체적으로 제시
3. 개선사항은 실용적이고 구체적으로 제시
4. 한국어로만 작성"""

    if model_type == "openai":
        if not OPENAI_AVAILABLE:
            raise ValueError("OpenAI 라이브러리가 설치되지 않았습니다. pip install openai")
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content.strip())
            
            # 비한국어 문자 제거 (pros, cons, improvement)
            # 파일 상단에서 이미 import re를 했으므로 함수 내부에서 다시 import할 필요 없음
            def remove_non_korean(text: str) -> str:
                if not isinstance(text, str):
                    return text
                text = re.sub(r'[\u4e00-\u9fff]+', '', text)  # 한자
                text = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', '', text)  # 일본어
                text = re.sub(r'[\u0400-\u04ff]+', '', text)  # 러시아어
                text = re.sub(r'[\u1e00-\u1eff\u0e00-\u0e7f\u0600-\u06ff]+', '', text)  # 기타
                return text
            
            if "pros" in result and isinstance(result["pros"], list):
                result["pros"] = [remove_non_korean(item) for item in result["pros"]]
            if "cons" in result and isinstance(result["cons"], list):
                result["cons"] = [remove_non_korean(item) for item in result["cons"]]
            if "improvement" in result and isinstance(result["improvement"], str):
                result["improvement"] = remove_non_korean(result["improvement"])
            
            return result
        except Exception as e:
            error_str = str(e)
            if "insufficient_quota" in error_str or "quota" in error_str.lower():
                raise ValueError("OpenAI API 할당량이 초과되었습니다. 계정의 결제 정보와 사용량을 확인해주세요. https://platform.openai.com/usage")
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                raise ValueError("OpenAI API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                raise ValueError("OpenAI API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"OpenAI API 오류: {error_str}")
    
    elif model_type == "groq":
        if not GROQ_AVAILABLE:
            raise ValueError("Groq 라이브러리가 설치되지 않았습니다. pip install groq")
        try:
            client = get_groq_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content.strip())
            
            # 비한국어 문자 제거 (pros, cons, improvement)
            # 파일 상단에서 이미 import re를 했으므로 함수 내부에서 다시 import할 필요 없음
            def remove_non_korean(text: str) -> str:
                if not isinstance(text, str):
                    return text
                text = re.sub(r'[\u4e00-\u9fff]+', '', text)  # 한자
                text = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', '', text)  # 일본어
                text = re.sub(r'[\u0400-\u04ff]+', '', text)  # 러시아어
                text = re.sub(r'[\u1e00-\u1eff\u0e00-\u0e7f\u0600-\u06ff]+', '', text)  # 기타
                return text
            
            if "pros" in result and isinstance(result["pros"], list):
                result["pros"] = [remove_non_korean(item) for item in result["pros"]]
            if "cons" in result and isinstance(result["cons"], list):
                result["cons"] = [remove_non_korean(item) for item in result["cons"]]
            if "improvement" in result and isinstance(result["improvement"], str):
                result["improvement"] = remove_non_korean(result["improvement"])
            
            return result
        except Exception as e:
            error_str = str(e)
            if "model_decommissioned" in error_str or "decommissioned" in error_str.lower():
                raise ValueError("사용 중인 Groq 모델이 더 이상 지원되지 않습니다. llama-3.3-70b-versatile 모델을 사용해주세요. https://console.groq.com/docs/deprecations")
            elif "rate_limit" in error_str.lower() or "429" in error_str:
                raise ValueError("Groq API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
            elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower():
                raise ValueError("Groq API 키가 유효하지 않습니다. API 키를 확인해주세요.")
            else:
                raise ValueError(f"Groq API 오류: {error_str}")
    
    elif model_type == "gemini":
        if not GEMINI_AVAILABLE:
            raise ValueError("Google Generative AI 라이브러리가 설치되지 않았습니다. pip install google-generativeai")
        model = get_gemini_client()
        response = model.generate_content(prompt)
        # JSON 추출
        text = response.text.strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # JSON 형식이 아니면 파싱 시도
            result = {"pros": [], "cons": [], "improvement": text}
        
        # 비한국어 문자 제거 (pros, cons, improvement)
        # 한자/일본어/중국어/러시아어/베트남어 등 비한글 문자 제거
        # 파일 상단에서 이미 import re를 했으므로 함수 내부에서 다시 import할 필요 없음
        def remove_non_korean(text: str) -> str:
            if not isinstance(text, str):
                return text
            # 한자 제거
            text = re.sub(r'[\u4e00-\u9fff]+', '', text)
            # 일본어 히라가나/가타카나 제거
            text = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', '', text)
            # 러시아어 키릴 문자 제거
            text = re.sub(r'[\u0400-\u04ff]+', '', text)
            # 베트남어/태국어/아랍어 등 기타 문자 제거
            text = re.sub(r'[\u1e00-\u1eff\u0e00-\u0e7f\u0600-\u06ff]+', '', text)
            return text
        
        # pros 리스트에서 비한국어 문자 제거
        if "pros" in result and isinstance(result["pros"], list):
            result["pros"] = [remove_non_korean(item) for item in result["pros"]]
        # cons 리스트에서 비한국어 문자 제거
        if "cons" in result and isinstance(result["cons"], list):
            result["cons"] = [remove_non_korean(item) for item in result["cons"]]
        # improvement 문자열에서 비한국어 문자 제거
        if "improvement" in result and isinstance(result["improvement"], str):
            result["improvement"] = remove_non_korean(result["improvement"])
        
        return result
    
    else:
        raise ValueError(f"지원하지 않는 모델 타입: {model_type}")


def generate_final(topic: str, article_intent: str, target_audience: str, tone_style: str, drafts: list, analyses: list) -> str:
    """
    3개 모델의 강점을 조합하여 최종 고품질 글 생성
    
    Args:
        topic: 주제
        article_intent: 글 의도
        target_audience: 대상 독자
        tone_style: 톤/스타일
        drafts: 초안 리스트 [{'model': '...', 'content': '...'}, ...]
        analyses: 분석 리스트 [{'model': '...', 'pros': [...], 'cons': [...], 'improvement': '...'}, ...]
    
    Returns:
        최종 완성 글
    """
    # 초안과 분석 내용 정리
    drafts_text = "\n\n".join([f"## {d['model']} 초안:\n{d['content']}" for d in drafts])
    analyses_text = "\n\n".join([
        f"## {a['model']} 분석:\n장점: {', '.join(a['pros'])}\n단점: {', '.join(a['cons'])}\n개선: {a['improvement']}"
        for a in analyses
    ])
    
    prompt = f"""다음 정보를 바탕으로 세 AI 모델의 강점을 모두 조합하여 최고 품질의 블로그 글을 작성해주세요.

주제: {topic}
글 의도: {article_intent}
대상 독자: {target_audience}
톤/스타일: {tone_style}

세 모델의 초안:
{drafts_text}

세 모델의 장단점 분석:
{analyses_text}

요구사항:
1. 세 모델의 장점을 모두 반영하여 작성
   - ChatGPT의 장점 활용
   - Gemini의 장점 활용
   - Groq의 장점 활용
2. 각 모델의 단점을 보완하여 작성
3. 각 모델의 개선사항을 반영
4. 대상 독자에게 맞는 수준과 톤으로 작성
5. 글 의도에 맞는 구조로 작성
6. 톤/스타일을 일관되게 유지
7. 한국어로만 작성 (한자, 외국어 사용 금지)
8. 3000-5000자 정도로 충실하게 작성
9. **중요: 마크다운 형식 사용 금지**
   - **볼드(**텍스트**)**, *이탤릭*, ### 헤딩, ## 소제목 등 텍스트 스타일링 마크다운 사용 금지
   - 해시태그(#컬쳐캐피탈)는 예외로 사용 가능
   - 일반 텍스트로만 작성 (줄바꿈은 엔터로 구분)

필수 구조:
1. 제목: 일반 텍스트로 제목 작성 (마크다운 # 사용 금지)
2. 서론: 2-3문단으로 독자의 관심을 끌고 주제를 소개
3. 본론: 
   - 일반 텍스트로 소제목 작성 (마크다운 ##, ### 사용 금지)
   - 구체적인 예시, 숫자, 사례 포함
   - 표는 일반 텍스트로 작성 (마크다운 테이블 형식 사용 금지)
   - 체크리스트나 불릿 포인트는 일반 텍스트로 작성
4. 핵심 요약: 불릿 포인트로 주요 내용 정리 (마크다운 사용 금지)
5. 결론: 2-3문단으로 마무리
6. 자주 묻는 질문 (FAQ): Q&A 형식으로 3-6개 질문과 답변
7. 태그: 해시태그 형식으로 5-10개 태그 (#컬쳐캐피탈 형식으로 작성)

글 흐름:
- 서론에서 독자의 문제나 관심사 제시
- 본론에서 단계별로 해결책 제시
- 구체적인 예시와 사례 포함
- 실전 팁과 체크리스트 제공
- 표를 활용한 정보 정리
- 친절하고 명확한 설명

최종 완성 글:"""

    # 최종 생성은 Gemini 사용
    if not GEMINI_AVAILABLE:
        raise ValueError("Google Generative AI 라이브러리가 설치되지 않았습니다. pip install google-generativeai")
    try:
        model = get_gemini_client()
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # 마크다운 스타일링 제거 (해시태그는 유지)
        import re
        # **볼드** 제거 (여러 줄에 걸쳐 있어도 처리)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content, flags=re.DOTALL)
        # *이탤릭* 제거 (단, **볼드**가 아닌 경우만)
        content = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'\1', content)
        # ### 헤딩 제거 (해시태그는 유지하기 위해 줄 시작에 #이 오는 경우만)
        content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
        # ## 소제목 제거
        content = re.sub(r'^##\s+', '', content, flags=re.MULTILINE)
        # ### 하위 소제목 제거
        content = re.sub(r'^###\s+', '', content, flags=re.MULTILINE)
        # #### 하위 소제목 제거
        content = re.sub(r'^####\s+', '', content, flags=re.MULTILINE)
        # ##### 하위 소제목 제거
        content = re.sub(r'^#####\s+', '', content, flags=re.MULTILINE)
        # ###### 하위 소제목 제거
        content = re.sub(r'^######\s+', '', content, flags=re.MULTILINE)
        # 남은 단독 * 제거 (볼드/이탤릭 마크다운)
        content = re.sub(r'\*([^*\n]+)\*', r'\1', content)
        # 남은 단독 ** 제거
        content = re.sub(r'\*\*([^*\n]+)\*\*', r'\1', content)
        
        # 한자/일본어/중국어/러시아어/베트남어 등 비한글 문자 제거
        # 한자 범위: \u4e00-\u9fff (CJK 통합 한자)
        # 히라가나: \u3040-\u309f
        # 가타카나: \u30a0-\u30ff
        # 키릴 문자(러시아어): \u0400-\u04ff
        # 베트남어 확장: \u1e00-\u1eff
        # 태국어: \u0e00-\u0e7f
        # 아랍어: \u0600-\u06ff
        
        # 한자 제거
        content = re.sub(r'[\u4e00-\u9fff]+', '', content)
        # 일본어 히라가나/가타카나 제거
        content = re.sub(r'[\u3040-\u309f\u30a0-\u30ff]+', '', content)
        # 러시아어 키릴 문자 제거
        content = re.sub(r'[\u0400-\u04ff]+', '', content)
        # 베트남어/태국어/아랍어 등 기타 문자 제거
        content = re.sub(r'[\u1e00-\u1eff\u0e00-\u0e7f\u0600-\u06ff]+', '', content)
        
        return content
    except Exception as e:
        error_str = str(e)
        if "quota" in error_str.lower() or "429" in error_str:
            raise ValueError("Gemini API 요청 한도가 초과되었습니다. 잠시 후 다시 시도해주세요.")
        elif "invalid_api_key" in error_str.lower() or "authentication" in error_str.lower() or "API key" in error_str:
            raise ValueError("Gemini API 키가 유효하지 않습니다. API 키를 확인해주세요.")
        else:
            raise ValueError(f"Gemini API 오류: {error_str}")
