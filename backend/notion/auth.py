# notion/auth.py
import os
try:
    from notion_client import Client
    import httpx
    
    # 환경 변수에서 API 키와 Database ID 읽기
    NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")
    
    notion = Client(auth=NOTION_API_KEY)
    NOTION_AVAILABLE = True
except ImportError:
    # notion_client가 설치되지 않은 경우
    NOTION_AVAILABLE = False
    notion = None
    import httpx  # httpx는 별도로 import 시도


def check_login(user_id, user_pw):
    if not NOTION_AVAILABLE:
        print("오류: notion_client 모듈이 설치되지 않았습니다.")
        print("해결 방법: python -m pip install notion-client")
        return False
    
    try:
        # ✅ notion-client API 사용 (여러 방법 시도)
        response = None
        
        # 방법 1: 표준 API 사용
        try:
            if hasattr(notion.databases, 'query'):
                response = notion.databases.query(database_id=DATABASE_ID)
            else:
                # 방법 2: 직접 HTTP 요청 (fallback)
                raise AttributeError("query method not found")
        except AttributeError:
            # 방법 3: 직접 HTTP API 호출
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
            
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json={})
                response.raise_for_status()
                response = response.json()
        
        # 결과 처리
        for row in response.get("results", []):
            props = row.get("properties", {})
            
            # 안전하게 데이터 접근
            try:
                db_id_prop = props.get("아이디", {}).get("title", [])
                db_pw_prop = props.get("비밀번호", {}).get("rich_text", [])
                
                if not db_id_prop or not db_pw_prop:
                    continue
                
                db_id = db_id_prop[0].get("text", {}).get("content", "")
                db_pw = db_pw_prop[0].get("text", {}).get("content", "")

                if user_id == db_id and user_pw == db_pw:
                    return True
            except (KeyError, IndexError, TypeError):
                continue

        return False

    except AttributeError as e:
        # 'DatabasesEndpoint' object has no attribute 'query' 오류 처리
        print(f"노션 API 오류: 라이브러리 버전 문제일 수 있습니다.")
        print(f"오류 상세: {e}")
        # HTTP 직접 호출로 재시도
        try:
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json={})
                response.raise_for_status()
                response = response.json()
            
            for row in response.get("results", []):
                props = row.get("properties", {})
                try:
                    db_id_prop = props.get("아이디", {}).get("title", [])
                    db_pw_prop = props.get("비밀번호", {}).get("rich_text", [])
                    
                    if not db_id_prop or not db_pw_prop:
                        continue
                    
                    db_id = db_id_prop[0].get("text", {}).get("content", "")
                    db_pw = db_pw_prop[0].get("text", {}).get("content", "")

                    if user_id == db_id and user_pw == db_pw:
                        return True
                except (KeyError, IndexError, TypeError):
                    continue
            return False
        except Exception as e2:
            print(f"HTTP 직접 호출도 실패: {e2}")
            return False
    except Exception as e:
        print(f"노션 로그인 오류: {e}")
        return False


def save_article_to_notion(
    user_id: str,
    topic: str,
    content: str,
    article_intent: str,
    target_audience: str,
    model: str,
    database_id: str = None
) -> bool:
    """
    생성된 글을 Notion Database에 저장
    
    Args:
        user_id: 사용자 ID
        topic: 주제
        content: 생성된 글 내용
        article_intent: 글 의도
        target_audience: 대상 독자
        model: 사용한 모델 (ChatGPT, Gemini, Groq)
        database_id: Notion Database ID (None이면 기본 DATABASE_ID 사용)
    
    Returns:
        저장 성공 여부
    """
    if not NOTION_AVAILABLE:
        print("오류: notion_client 모듈이 설치되지 않았습니다.")
        return False
    
    try:
        # Database ID가 제공되지 않으면 기본값 사용
        target_db_id = database_id or DATABASE_ID
        
        # Notion API로 페이지 생성
        from datetime import datetime
        
        # 방법 1: notion-client 사용
        try:
            new_page = notion.pages.create(
                parent={"database_id": target_db_id},
                properties={
                    "제목": {
                        "title": [
                            {
                                "text": {
                                    "content": topic[:200]  # 제목은 200자 제한
                                }
                            }
                        ]
                    },
                    "주제": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": topic
                                }
                            }
                        ]
                    },
                    "내용": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": content[:2000]  # 내용은 2000자로 제한 (더 길면 잘림)
                                }
                            }
                        ]
                    },
                    "생성일": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    },
                    "사용자": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user_id
                                }
                            }
                        ]
                    },
                    "모델": {
                        "select": {
                            "name": model
                        }
                    },
                    "글 의도": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": article_intent
                                }
                            }
                        ]
                    },
                    "대상 독자": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": target_audience
                                }
                            }
                        ]
                    }
                },
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content  # 전체 내용은 페이지 본문에
                                    }
                                }
                            ]
                        }
                    }
                ]
            )
            return True
        except Exception as e:
            print(f"notion-client로 저장 실패, HTTP 직접 호출 시도: {e}")
            # 방법 2: HTTP 직접 호출
            import httpx
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            # 내용이 너무 길면 잘라서 저장
            content_preview = content[:2000] if len(content) > 2000 else content
            
            payload = {
                "parent": {"database_id": target_db_id},
                "properties": {
                    "제목": {
                        "title": [
                            {
                                "text": {
                                    "content": topic[:200]
                                }
                            }
                        ]
                    },
                    "주제": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": topic
                                }
                            }
                        ]
                    },
                    "내용": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": content_preview
                                }
                            }
                        ]
                    },
                    "생성일": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    },
                    "사용자": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user_id
                                }
                            }
                        ]
                    },
                    "모델": {
                        "select": {
                            "name": model
                        }
                    },
                    "글 의도": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": article_intent
                                }
                            }
                        ]
                    },
                    "대상 독자": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": target_audience
                                }
                            }
                        ]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            url = "https://api.notion.com/v1/pages"
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            return True
            
    except Exception as e:
        print(f"Notion에 글 저장 실패: {e}")
        return False


def save_usage_log_to_notion(
    user_id: str,
    action_type: str,  # '초안생성', '장단점분석', '최종글생성'
    model: str,
    topic: str,
    database_id: str = None
) -> bool:
    """
    사용 기록을 Notion Database에 저장
    
    Args:
        user_id: 사용자 ID
        action_type: 작업 유형
        model: 사용한 모델
        topic: 주제
        database_id: Notion Database ID (사용 기록용)
    
    Returns:
        저장 성공 여부
    """
    if not NOTION_AVAILABLE:
        return False
    
    try:
        from datetime import datetime
        target_db_id = database_id or DATABASE_ID
        
        # 방법 1: notion-client 사용
        try:
            new_page = notion.pages.create(
                parent={"database_id": target_db_id},
                properties={
                    "사용자": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user_id
                                }
                            }
                        ]
                    },
                    "작업 유형": {
                        "select": {
                            "name": action_type
                        }
                    },
                    "사용 모델": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": model
                                }
                            }
                        ]
                    },
                    "생성일시": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    },
                    "주제": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": topic
                                }
                            }
                        ]
                    }
                }
            )
            return True
        except Exception as e:
            print(f"notion-client로 저장 실패, HTTP 직접 호출 시도: {e}")
            # 방법 2: HTTP 직접 호출
            import httpx
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            payload = {
                "parent": {"database_id": target_db_id},
                "properties": {
                    "사용자": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": user_id
                                }
                            }
                        ]
                    },
                    "작업 유형": {
                        "select": {
                            "name": action_type
                        }
                    },
                    "사용 모델": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": model
                                }
                            }
                        ]
                    },
                    "생성일시": {
                        "date": {
                            "start": datetime.now().isoformat()
                        }
                    },
                    "주제": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": topic
                                }
                            }
                        ]
                    }
                }
            }
            
            url = "https://api.notion.com/v1/pages"
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            return True
            
    except Exception as e:
        print(f"Notion에 사용 기록 저장 실패: {e}")
        return False


def get_user_articles(user_id: str, database_id: str = None) -> list:
    """
    사용자별로 생성된 글 목록 조회
    
    Args:
        user_id: 사용자 ID
        database_id: Notion Database ID (None이면 기본 DATABASE_ID 사용)
    
    Returns:
        사용자가 생성한 글 목록 (dict 리스트)
    """
    if not NOTION_AVAILABLE:
        print("오류: notion_client 모듈이 설치되지 않았습니다.")
        return []
    
    try:
        target_db_id = database_id or DATABASE_ID
        
        # 방법 1: notion-client 사용
        try:
            response = notion.databases.query(
                database_id=target_db_id,
                filter={
                    "property": "사용자",
                    "rich_text": {
                        "equals": user_id
                    }
                },
                sorts=[
                    {
                        "property": "생성일",
                        "direction": "descending"
                    }
                ]
            )
            
            articles = []
            for page in response.get("results", []):
                props = page.get("properties", {})
                try:
                    # 제목 추출
                    title_prop = props.get("제목", {}).get("title", [])
                    title = title_prop[0].get("text", {}).get("content", "") if title_prop else ""
                    
                    # 주제 추출
                    topic_prop = props.get("주제", {}).get("rich_text", [])
                    topic = topic_prop[0].get("text", {}).get("content", "") if topic_prop else ""
                    
                    # 내용 추출
                    content_prop = props.get("내용", {}).get("rich_text", [])
                    content = content_prop[0].get("text", {}).get("content", "") if content_prop else ""
                    
                    # 생성일 추출
                    date_prop = props.get("생성일", {}).get("date", {})
                    created_date = date_prop.get("start", "") if date_prop else ""
                    
                    # 모델 추출
                    model_prop = props.get("모델", {}).get("select", {})
                    model = model_prop.get("name", "") if model_prop else ""
                    
                    # 글 의도 추출
                    intent_prop = props.get("글 의도", {}).get("rich_text", [])
                    article_intent = intent_prop[0].get("text", {}).get("content", "") if intent_prop else ""
                    
                    # 대상 독자 추출
                    audience_prop = props.get("대상 독자", {}).get("rich_text", [])
                    target_audience = audience_prop[0].get("text", {}).get("content", "") if audience_prop else ""
                    
                    # 페이지 ID
                    page_id = page.get("id", "")
                    
                    articles.append({
                        "id": page_id,
                        "title": title,
                        "topic": topic,
                        "content": content,
                        "created_date": created_date,
                        "model": model,
                        "article_intent": article_intent,
                        "target_audience": target_audience
                    })
                except (KeyError, IndexError, TypeError) as e:
                    print(f"페이지 파싱 오류: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            print(f"notion-client로 조회 실패, HTTP 직접 호출 시도: {e}")
            # 방법 2: HTTP 직접 호출
            import httpx
            headers = {
                "Authorization": f"Bearer {NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            url = f"https://api.notion.com/v1/databases/{target_db_id}/query"
            payload = {
                "filter": {
                    "property": "사용자",
                    "rich_text": {
                        "equals": user_id
                    }
                },
                "sorts": [
                    {
                        "property": "생성일",
                        "direction": "descending"
                    }
                ]
            }
            
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
            
            articles = []
            for page in response_data.get("results", []):
                props = page.get("properties", {})
                try:
                    title_prop = props.get("제목", {}).get("title", [])
                    title = title_prop[0].get("text", {}).get("content", "") if title_prop else ""
                    
                    topic_prop = props.get("주제", {}).get("rich_text", [])
                    topic = topic_prop[0].get("text", {}).get("content", "") if topic_prop else ""
                    
                    content_prop = props.get("내용", {}).get("rich_text", [])
                    content = content_prop[0].get("text", {}).get("content", "") if content_prop else ""
                    
                    date_prop = props.get("생성일", {}).get("date", {})
                    created_date = date_prop.get("start", "") if date_prop else ""
                    
                    model_prop = props.get("모델", {}).get("select", {})
                    model = model_prop.get("name", "") if model_prop else ""
                    
                    intent_prop = props.get("글 의도", {}).get("rich_text", [])
                    article_intent = intent_prop[0].get("text", {}).get("content", "") if intent_prop else ""
                    
                    audience_prop = props.get("대상 독자", {}).get("rich_text", [])
                    target_audience = audience_prop[0].get("text", {}).get("content", "") if audience_prop else ""
                    
                    page_id = page.get("id", "")
                    
                    articles.append({
                        "id": page_id,
                        "title": title,
                        "topic": topic,
                        "content": content,
                        "created_date": created_date,
                        "model": model,
                        "article_intent": article_intent,
                        "target_audience": target_audience
                    })
                except (KeyError, IndexError, TypeError) as e:
                    print(f"페이지 파싱 오류: {e}")
                    continue
            
            return articles
            
    except Exception as e:
        print(f"Notion에서 글 조회 실패: {e}")
        return []
