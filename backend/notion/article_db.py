# notion/article_db.py
# 기록 저장용 Notion Database 설정
import os
try:
    from notion_client import Client
    import httpx
    
    # 기록 저장용 API 키 (환경 변수에서 읽기)
    ARTICLE_NOTION_API_KEY = os.getenv("ARTICLE_NOTION_API_KEY", "")
    
    # 기록 저장용 Database ID (환경 변수에서 읽기)
    # URL: https://www.notion.so/2eabe3c7b25480a5b8e2fbb68b891e77?v=2eabe3c7b254809a8747000c0cfa9791
    # Database ID는 URL의 첫 번째 부분입니다
    ARTICLE_DATABASE_ID = os.getenv("ARTICLE_DATABASE_ID", "")
    
    article_notion = Client(auth=ARTICLE_NOTION_API_KEY)
    ARTICLE_NOTION_AVAILABLE = True
except ImportError:
    ARTICLE_NOTION_AVAILABLE = False
    article_notion = None
    import httpx


def _split_content_into_blocks(content: str, max_length: int = 2000) -> list:
    """
    긴 텍스트를 Notion API 제한(2000자)에 맞게 여러 블록으로 분할
    
    Args:
        content: 원본 텍스트 내용
        max_length: 블록당 최대 문자 수 (기본값: 2000)
    
    Returns:
        블록 리스트
    """
    if len(content) <= max_length:
        return [
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
    
    # 텍스트를 여러 블록으로 분할
    blocks = []
    lines = content.split('\n')
    current_block = ""
    
    for line in lines:
        # 현재 블록에 이 줄을 추가했을 때 제한을 초과하는지 확인
        if len(current_block) + len(line) + 1 > max_length:
            # 현재 블록이 비어있지 않으면 저장
            if current_block:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": current_block.rstrip()
                                }
                            }
                        ]
                    }
                })
            # 현재 줄이 제한보다 길면 더 작게 나눔
            if len(line) > max_length:
                # 줄을 단어 단위로 나누되, 제한 내에서 가능한 만큼
                words = line.split(' ')
                temp_line = ""
                for word in words:
                    if len(temp_line) + len(word) + 1 > max_length:
                        if temp_line:
                            blocks.append({
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": temp_line.rstrip()
                                            }
                                        }
                                    ]
                                }
                            })
                        temp_line = word
                    else:
                        temp_line += (" " + word if temp_line else word)
                current_block = temp_line
            else:
                current_block = line
        else:
            current_block += ("\n" + line if current_block else line)
    
    # 마지막 블록 저장
    if current_block:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": current_block.rstrip()
                        }
                    }
                ]
            }
        })
    
    return blocks if blocks else [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content[:max_length]
                        }
                    }
                ]
            }
        }
    ]


def save_article_to_notion_db(
    user_id: str,
    topic: str,
    content: str,
    article_intent: str,
    target_audience: str,
    model: str,
    database_id: str = None,
    article_type: str = "최종글"  # "초안" 또는 "최종글"
) -> bool:
    """
    생성된 글을 Notion Database에 저장 (기록용)
    
    Args:
        user_id: 사용자 ID
        topic: 주제
        content: 생성된 글 내용
        article_intent: 글 의도
        target_audience: 대상 독자
        model: 사용한 모델 (ChatGPT, Gemini, Groq)
        database_id: Notion Database ID (None이면 기본 ARTICLE_DATABASE_ID 사용)
    
    Returns:
        저장 성공 여부
    """
    if not ARTICLE_NOTION_AVAILABLE:
        print("오류: notion_client 모듈이 설치되지 않았습니다.")
        return False
    
    if not ARTICLE_DATABASE_ID and not database_id:
        print("오류: Database ID가 설정되지 않았습니다. ARTICLE_DATABASE_ID를 설정하거나 database_id를 제공하세요.")
        return False
    
    try:
        # Database ID가 제공되지 않으면 기본값 사용
        target_db_id = database_id or ARTICLE_DATABASE_ID
        
        # Notion API로 페이지 생성
        from datetime import datetime, timezone, timedelta
        
        # 방법 1: notion-client 사용
        try:
            new_page = article_notion.pages.create(
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
                        "rich_text": [
                            {
                                "text": {
                                    "content": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
                                }
                            }
                        ]
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
                    },
                    "유형": {
                        "select": {
                            "name": article_type
                        }
                    }
                },
                children=_split_content_into_blocks(content)  # 긴 내용을 여러 블록으로 분할
            )
            print(f"✅ notion-client로 저장 성공: {topic[:50]}...")
            return True
        except Exception as e:
            print(f"⚠️ notion-client로 저장 실패, HTTP 직접 호출 시도: {e}")
            import traceback
            traceback.print_exc()
            # 방법 2: HTTP 직접 호출
            headers = {
                "Authorization": f"Bearer {ARTICLE_NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
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
                                    "content": content[:2000]  # 미리보기용 (2000자 제한)
                                }
                            }
                        ]
                    },
                    "생성일": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
                                }
                            }
                        ]
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
                    },
                    "유형": {
                        "select": {
                            "name": article_type
                        }
                    }
                },
                "children": _split_content_into_blocks(content)  # 긴 내용을 여러 블록으로 분할
            }
            
            url = "https://api.notion.com/v1/pages"
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            print(f"✅ HTTP 직접 호출로 저장 성공: {topic[:50]}...")
            return True
            
    except Exception as e:
        print(f"❌ Notion에 글 저장 실패: {e}")
        print(f"   Database ID: {target_db_id}")
        print(f"   API Key: {ARTICLE_NOTION_API_KEY[:20]}...")
        import traceback
        traceback.print_exc()
        return False


def _get_page_content(page_id: str) -> str:
    """
    페이지 본문(blocks)에서 전체 내용을 추출
    
    Args:
        page_id: Notion 페이지 ID
    
    Returns:
        페이지 본문의 전체 텍스트 내용
    """
    try:
        headers = {
            "Authorization": f"Bearer {ARTICLE_NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
        }
        
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        content_parts = []
        
        with httpx.Client() as client:
            # 페이지네이션 처리
            next_cursor = None
            while True:
                params = {}
                if next_cursor:
                    params["start_cursor"] = next_cursor
                
                response = client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                # 각 블록에서 텍스트 추출
                for block in data.get("results", []):
                    block_type = block.get("type", "")
                    if block_type == "paragraph":
                        rich_text = block.get("paragraph", {}).get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(text_item.get("text", {}).get("content", ""))
                    elif block_type == "heading_1":
                        rich_text = block.get("heading_1", {}).get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(f"# {text_item.get('text', {}).get('content', '')}\n")
                    elif block_type == "heading_2":
                        rich_text = block.get("heading_2", {}).get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(f"## {text_item.get('text', {}).get('content', '')}\n")
                    elif block_type == "heading_3":
                        rich_text = block.get("heading_3", {}).get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(f"### {text_item.get('text', {}).get('content', '')}\n")
                    elif block_type == "bulleted_list_item":
                        rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(f"- {text_item.get('text', {}).get('content', '')}\n")
                    elif block_type == "numbered_list_item":
                        rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(f"1. {text_item.get('text', {}).get('content', '')}\n")
                    else:
                        # 기타 블록 타입도 텍스트 추출 시도
                        block_data = block.get(block_type, {})
                        rich_text = block_data.get("rich_text", [])
                        for text_item in rich_text:
                            if text_item.get("type") == "text":
                                content_parts.append(text_item.get("text", {}).get("content", ""))
                
                # 다음 페이지 확인
                if data.get("has_more"):
                    next_cursor = data.get("next_cursor")
                else:
                    break
        
        return "\n".join(content_parts)
    except Exception as e:
        print(f"페이지 본문 가져오기 실패: {e}")
        return ""


def get_user_articles_from_notion_db(
    user_id: str,
    database_id: str = None,
    article_type: str = "최종글"  # 기본값: "최종글"만 조회
) -> list:
    """
    사용자별로 생성된 글 목록 조회 (기록용 Database에서)
    페이지 본문에서 전체 내용을 가져옵니다.
    
    Args:
        user_id: 사용자 ID
        database_id: Notion Database ID (None이면 기본 ARTICLE_DATABASE_ID 사용)
    
    Returns:
        사용자가 생성한 글 목록 (dict 리스트)
    """
    if not ARTICLE_NOTION_AVAILABLE:
        print("오류: notion_client 모듈이 설치되지 않았습니다.")
        return []
    
    if not ARTICLE_DATABASE_ID and not database_id:
        print("오류: Database ID가 설정되지 않았습니다.")
        return []
    
    try:
        target_db_id = database_id or ARTICLE_DATABASE_ID
        
        # HTTP 직접 호출만 사용 (notion-client의 query 메서드가 안정적이지 않음)
        try:
            headers = {
                "Authorization": f"Bearer {ARTICLE_NOTION_API_KEY}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            url = f"https://api.notion.com/v1/databases/{target_db_id}/query"
            
            # 필터 조건 구성: "유형" 필드가 없을 수 있으므로 사용자만 필터링하고, 나중에 코드에서 유형 필터링
            filter_conditions = {
                "property": "사용자",
                "rich_text": {
                    "equals": user_id
                }
            }
            
            payload = {
                "filter": filter_conditions,
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
                    # 제목 추출
                    title_prop = props.get("제목", {}).get("title", [])
                    title = title_prop[0].get("text", {}).get("content", "") if title_prop else ""
                    
                    # 주제 추출
                    topic_prop = props.get("주제", {}).get("rich_text", [])
                    topic = topic_prop[0].get("text", {}).get("content", "") if topic_prop else ""
                    
                    # 페이지 ID
                    page_id = page.get("id", "")
                    
                    # "유형" 필터 적용: article_type이 지정된 경우 "유형" 필드 확인
                    if article_type:
                        type_prop = props.get("유형", {}).get("select", {})
                        page_article_type = type_prop.get("name", "") if type_prop else ""
                        # 유형이 일치하지 않으면 건너뛰기
                        if page_article_type != article_type:
                            continue
                    
                    # 페이지 본문에서 전체 내용 가져오기
                    content = _get_page_content(page_id)
                    
                    # 본문이 없으면 속성의 "내용" 필드 사용 (미리보기용)
                    if not content:
                        content_prop = props.get("내용", {}).get("rich_text", [])
                        content = content_prop[0].get("text", {}).get("content", "") if content_prop else ""
                    
                    # 생성일 추출 (rich_text 타입)
                    date_prop = props.get("생성일", {}).get("rich_text", [])
                    created_date = date_prop[0].get("text", {}).get("content", "") if date_prop else ""
                    
                    # 모델 추출
                    model_prop = props.get("모델", {}).get("select", {})
                    model = model_prop.get("name", "") if model_prop else ""
                    
                    # 글 의도 추출
                    intent_prop = props.get("글 의도", {}).get("rich_text", [])
                    article_intent = intent_prop[0].get("text", {}).get("content", "") if intent_prop else ""
                    
                    # 대상 독자 추출
                    audience_prop = props.get("대상 독자", {}).get("rich_text", [])
                    target_audience = audience_prop[0].get("text", {}).get("content", "") if audience_prop else ""
                    
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
            print(f"HTTP 직접 호출로 글 조회 실패: {e}")
            return []
            
    except Exception as e:
        print(f"Notion에서 글 조회 실패: {e}")
        return []
