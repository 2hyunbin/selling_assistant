# PRD: 중고거래 AI 에이전트 챗봇

## 1. 프로젝트 개요

### 1.1 목적
중고거래 플랫폼 판매자가 자연어로 매물을 관리하고, AI가 자동으로 가격 조정, 끌어올리기, 글 수정 등을 수행하는 대화형 에이전트 시스템 구축

### 1.2 타겟
- 졸업 프로젝트 데모
- 로컬 환경 실행
- 단일 사용자 시나리오

### 1.3 핵심 가치
- **자동화**: "어제 올린 물건 가격 10% 낮춰줘" → AI가 데이터 조회 후 자동 실행
- **인사이트**: 시장 시세 분석 제공으로 의사결정 지원
- **직관성**: 채팅 인터페이스로 복잡한 관리 작업 단순화

---

## 2. 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.10+ |
| 백엔드 | FastAPI |
| LLM | Google Gemini API |
| 데이터베이스 | SQLite |
| 프론트엔드 | HTML/CSS/JavaScript (Vanilla 또는 간단한 템플릿) |

---

## 3. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend UI                        │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │   Chat Panel     │         │   User Info      │     │
│  │   (좌측)         │         │   Panel (우측)   │     │
│  │                  │         │                  │     │
│  │  - 대화 기록     │         │  - 판매중 매물   │     │
│  │  - 추천 액션버튼 │         │  - 실시간 업데이트│     │
│  └──────────────────┘         └──────────────────┘     │
└─────────────────────────────────────────────────────────┘
                         ↕ WebSocket/HTTP
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │           LLM Agent (Gemini API)                  │  │
│  │  1. Intent 분류                                   │  │
│  │  2. Slot 추출                                     │  │
│  │  3. Tool 선택                                     │  │
│  │  4. 실행 순서 결정                                │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↓                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Tool Executor                        │  │
│  │  - query_listings()                               │  │
│  │  - adjust_price()                                 │  │
│  │  - boost_listing()                                │  │
│  │  - update_content()                               │  │
│  │  - get_market_insights()                          │  │
│  └───────────────────────────────────────────────────┘  │
│                         ↓                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │              SQLite Database                      │  │
│  │  - listings (매물 테이블)                         │  │
│  │  - chat_history (대화 기록, Optional)             │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 데이터 모델

### 4.1 Listings (매물 테이블)

```sql
CREATE TABLE listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    price INTEGER NOT NULL,
    category TEXT NOT NULL,
    region TEXT NOT NULL,
    status TEXT DEFAULT 'active', -- active, sold
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_boosted_at TIMESTAMP NULL,
    boost_count INTEGER DEFAULT 0
);
```

**필드 설명**:
- `title`: 매물 제목
- `content`: 매물 설명
- `price`: 가격 (원)
- `category`: 카테고리 (예: 전자기기, 가구, 의류 등)
- `region`: 지역 (예: 강남구, 서초구 등)
- `status`: 판매 상태
- `last_boosted_at`: 마지막 끌어올리기 시간
- `boost_count`: 끌어올리기 횟수

### 4.2 Chat History (Optional - 컨텍스트 유지용)

```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL, -- user, assistant
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. 핵심 기능 명세

### 5.1 Intent 분류 (LLM Agent)

**지원 Intent**:
1. **QUERY_LISTINGS**: 매물 조회
   - 예: "어제 올린 물건 보여줘", "전자기기 카테고리 매물 알려줘"
2. **ADJUST_PRICE**: 가격 조정
   - 예: "맥북 가격 10% 낮춰줘", "ID 3번 매물 5만원 인하"
3. **BOOST_LISTING**: 끌어올리기
   - 예: "가장 오래된 매물 끌어올려줘", "노트북 끌올"
4. **UPDATE_CONTENT**: 글 수정
   - 예: "제목을 더 매력적으로 바꿔줘", "설명 추가해줘"
5. **GET_INSIGHTS**: 시장 인사이트 조회
   - 예: "노트북 시세 알려줘", "강남구 전자기기 평균가는?"
6. **GENERAL_CHAT**: 일반 대화
   - 예: "안녕", "고마워"

### 5.2 Slot 추출

각 Intent별 필요한 파라미터:

```python
# QUERY_LISTINGS
{
    "time_filter": "어제|오늘|최근 3일",  # optional
    "category": "전자기기|가구|의류",     # optional
    "region": "강남구|서초구",           # optional
}

# ADJUST_PRICE
{
    "listing_id": int,           # 명시적 ID 또는 쿼리 조건으로 추론
    "adjustment_type": "percent|absolute",
    "amount": float,             # -10 (10% 인하) 또는 -50000 (5만원 인하)
}

# BOOST_LISTING
{
    "listing_id": int,           # 추론 가능
}

# UPDATE_CONTENT
{
    "listing_id": int,
    "field": "title|content",
    "new_value": str,            # 또는 "제목 개선해줘" → LLM이 생성
}

# GET_INSIGHTS
{
    "category": str,
    "region": str,
}
```

### 5.3 Tool 정의

#### Tool 1: `query_listings`
**목적**: 조건에 맞는 매물 조회

**입력**:
```python
{
    "time_filter": Optional[str],  # "yesterday", "today", "last_3_days"
    "category": Optional[str],
    "region": Optional[str],
    "status": Optional[str] = "active"
}
```

**출력**:
```python
[
    {
        "id": 1,
        "title": "맥북 프로 16인치 팝니다",
        "price": 2000000,
        "category": "전자기기",
        "created_at": "2025-10-25T10:30:00"
    }
]
```

#### Tool 2: `adjust_price`
**목적**: 매물 가격 변경

**입력**:
```python
{
    "listing_id": int,
    "new_price": int  # 최종 가격 (계산 완료된 값)
}
```

**출력**:
```python
{
    "success": True,
    "old_price": 2000000,
    "new_price": 1800000,
    "change_percent": -10.0
}
```

**정책**:
- 가격 인하 10% 이상 권장 (프롬프트에 명시)
- 0원 이하 불가

#### Tool 3: `boost_listing`
**목적**: 매물 끌어올리기 (타임스탬프 갱신)

**입력**:
```python
{
    "listing_id": int
}
```

**출력**:
```python
{
    "success": True,
    "boosted_at": "2025-10-26T14:20:00",
    "message": "끌어올리기 완료"
}
```

**정책**:
- 하루 1회 제한 (마지막 끌올 후 24시간 경과 체크)
- 제한 위반 시 `success: False` + 경고 메시지

#### Tool 4: `update_content`
**목적**: 제목/내용 수정

**입력**:
```python
{
    "listing_id": int,
    "title": Optional[str],
    "content": Optional[str]
}
```

**출력**:
```python
{
    "success": True,
    "updated_fields": ["title"]
}
```

#### Tool 5: `get_market_insights`
**목적**: 시장 시세 정보 제공 (고정값 응답)

**입력**:
```python
{
    "category": str,
    "region": str
}
```

**출력** (예시):
```python
{
    "average_price": 850000,
    "avg_sell_days": 3,
    "sample_count": 42,  # 의미 없는 고정값
    "trend": "하락세",
    "recommendation": "현재 시세보다 5-10% 낮게 책정 추천"
}
```

**고정 데이터 매핑**:
```python
INSIGHTS_DATA = {
    ("전자기기", "강남구"): {"average_price": 850000, "avg_sell_days": 3, "trend": "하락세"},
    ("전자기기", "서초구"): {"average_price": 780000, "avg_sell_days": 4, "trend": "보합"},
    ("가구", "강남구"): {"average_price": 320000, "avg_sell_days": 7, "trend": "상승세"},
    ("의류", "강남구"): {"average_price": 45000, "avg_sell_days": 2, "trend": "하락세"},
    # 기본값
    ("default", "default"): {"average_price": 500000, "avg_sell_days": 5, "trend": "보합"}
}
```

---

## 6. LLM Agent 프롬프트 설계

### 6.1 System Prompt

```
당신은 중고거래 플랫폼의 AI 판매 어시스턴트입니다.

[역할]
- 사용자의 자연어 요청을 분석하여 적절한 액션을 실행합니다.
- 항상 친절하고 명확하게 응답합니다.

[사용 가능한 Tools]
1. query_listings: 매물 조회
2. adjust_price: 가격 조정
3. boost_listing: 끌어올리기
4. update_content: 제목/내용 수정
5. get_market_insights: 시장 시세 조회

[정책]
- 끌어올리기는 하루 1회만 가능합니다.
- 가격 인하 시 10% 이상 권장합니다.
- 가격은 0원 이하로 설정할 수 없습니다.

[응답 형식]
반드시 JSON 형식으로 응답하세요:
{
    "intent": "QUERY_LISTINGS | ADJUST_PRICE | BOOST_LISTING | UPDATE_CONTENT | GET_INSIGHTS | GENERAL_CHAT",
    "slots": { ... },
    "tools": [
        {"name": "tool_name", "params": { ... }}
    ],
    "response_text": "사용자에게 보여줄 응답",
    "reasoning": "왜 이 액션을 선택했는지 근거",
    "suggested_actions": [
        {"label": "가격 5% 더 인하", "action": "adjust_price", "params": {...}},
        {"label": "끌어올리기", "action": "boost_listing", "params": {...}}
    ]
}

[현재 날짜]
{current_date}

[사용자 매물 목록]
{listings_summary}
```

### 6.2 User Prompt 예시

```
사용자: 어제 올린 물건 가격 10% 낮춰줘

--- LLM 응답 예시 ---
{
    "intent": "ADJUST_PRICE",
    "slots": {
        "time_filter": "yesterday",
        "adjustment_type": "percent",
        "amount": -10
    },
    "tools": [
        {"name": "query_listings", "params": {"time_filter": "yesterday"}},
        {"name": "adjust_price", "params": {"listing_id": 3, "new_price": 1800000}}
    ],
    "response_text": "어제 등록하신 '맥북 프로 16인치' 매물의 가격을 200만원에서 180만원으로 10% 인하했습니다.",
    "reasoning": "사용자가 '어제 올린 물건'이라고 했으므로 created_at 기준으로 조회 후, 해당 매물(ID 3)의 가격을 10% 인하했습니다.",
    "suggested_actions": [
        {"label": "끌어올리기", "action": "boost_listing", "params": {"listing_id": 3}},
        {"label": "제목 개선 제안", "action": "update_content", "params": {"listing_id": 3, "field": "title"}}
    ]
}
```

---

## 7. API 명세

### 7.1 POST `/chat`

**요청**:
```json
{
    "message": "어제 올린 물건 가격 10% 낮춰줘"
}
```

**응답**:
```json
{
    "response": "어제 등록하신 '맥북 프로 16인치' 매물의 가격을 200만원에서 180만원으로 10% 인하했습니다.",
    "reasoning": "사용자가 '어제 올린 물건'이라고 했으므로...",
    "actions_taken": [
        {"tool": "query_listings", "result": [...]},
        {"tool": "adjust_price", "result": {"old_price": 2000000, "new_price": 1800000}}
    ],
    "suggested_actions": [
        {"label": "끌어올리기", "action": "boost_listing", "params": {"listing_id": 3}}
    ],
    "updated_listings": [3]  // 변경된 매물 ID 목록
}
```

### 7.2 GET `/listings`

**응답**:
```json
[
    {
        "id": 1,
        "title": "맥북 프로 16인치 팝니다",
        "price": 1800000,
        "category": "전자기기",
        "region": "강남구",
        "status": "active",
        "created_at": "2025-10-25T10:30:00",
        "last_boosted_at": null,
        "boost_count": 0
    }
]
```

### 7.3 POST `/listings` (초기 데이터 생성용)

**요청**:
```json
{
    "title": "아이폰 15 Pro",
    "content": "거의 새 것입니다",
    "price": 1200000,
    "category": "전자기기",
    "region": "강남구"
}
```

---

## 8. UI 설계

### 8.1 레이아웃

```
┌─────────────────────────────────────────────────────────────┐
│                     중고거래 AI 어시스턴트                    │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│   💬 채팅 영역 (50%)     │   📊 내 매물 현황 (50%)         │
│                          │                                  │
│  ┌────────────────────┐  │  ┌────────────────────────────┐ │
│  │ AI: 무엇을 도와    │  │  │  📦 맥북 프로 16인치       │ │
│  │     드릴까요?      │  │  │  💰 180만원 (-10% ↓)       │ │
│  └────────────────────┘  │  │  📍 강남구 | 전자기기      │ │
│                          │  │  🕒 어제 등록              │ │
│  ┌────────────────────┐  │  │  [끌어올리기] [수정]       │ │
│  │ User: 어제 올린    │  │  └────────────────────────────┘ │
│  │ 물건 가격 10% 낮춰 │  │                                  │
│  └────────────────────┘  │  ┌────────────────────────────┐ │
│                          │  │  📦 삼성 모니터 27인치     │ │
│  ┌────────────────────┐  │  │  💰 35만원                 │ │
│  │ AI: 가격을 180만원 │  │  │  📍 서초구 | 전자기기      │ │
│  │ 으로 인하했습니다  │  │  │  🕒 3일 전 등록            │ │
│  │                    │  │  │  [끌어올리기] [수정]       │ │
│  │ 💡 추천 액션:      │  │  └────────────────────────────┘ │
│  │ [끌어올리기]       │  │                                  │
│  │ [제목 개선]        │  │  ✨ 총 2개 매물 판매중          │
│  └────────────────────┘  │                                  │
│                          │                                  │
│  ┌────────────────────┐  │                                  │
│  │ [메시지 입력...]   │  │                                  │
│  └────────────────────┘  │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

### 8.2 실시간 업데이트

**우측 매물 패널**은 `/chat` API 응답의 `updated_listings` 배열을 받아:
1. 해당 ID의 매물만 `/listings/{id}` GET 요청으로 재조회
2. 가격 변경 시 애니메이션 효과 (예: 숫자 카운트업)
3. 끌어올리기 시 "🔥 방금 끌어올림" 배지 표시

---

## 9. 구현 우선순위

### Phase 1: MVP Core (필수)
- [x] SQLite DB 스키마 생성
- [x] FastAPI 기본 서버 (CORS 설정)
- [x] Gemini API 연동
- [x] Intent 분류 + Tool 실행 로직
- [x] 5가지 Tool 구현
- [x] 기본 UI (HTML/CSS/JS)

### Phase 2: UX 개선 (선택)
- [ ] 대화 컨텍스트 유지 (chat_history 테이블)
- [ ] 추천 액션 버튼 자동 생성
- [ ] 매물 카드 애니메이션
- [ ] 에러 핸들링 (끌올 제한 등)

### Phase 3: 고도화 (시간 여유 시)
- [ ] 다중 매물 일괄 처리 ("모든 전자기기 5% 인하")
- [ ] 글 자동 생성 기능 (LLM으로 제목/설명 작성)
- [ ] 통계 대시보드

---

## 10. 샘플 시나리오

### 시나리오 1: 가격 조정
```
User: 맥북 가격 너무 비싼 것 같아. 10% 낮춰줘
AI:   맥북 프로 16인치 매물의 가격을 200만원에서 180만원으로 인하했습니다.
      현재 강남구 전자기기 평균 시세는 85만원이며, 프리미엄 제품을 고려하면 적정 가격입니다.

      💡 추천 액션:
      [끌어올리기] [제목에 '급매' 추가]
```

### 시나리오 2: 끌어올리기
```
User: 가장 오래된 매물 끌어올려줘
AI:   3일 전 등록하신 '삼성 모니터 27인치' 매물을 끌어올렸습니다.

      ⚠️ 끌어올리기는 하루 1회만 가능하니 24시간 후 다시 이용해주세요.

      💡 추천 액션:
      [가격 5% 인하] [시세 확인]
```

### 시나리오 3: 시장 인사이트
```
User: 전자기기 시세 알려줘
AI:   강남구 전자기기 카테고리 분석 결과입니다:

      📊 평균 거래가: 85만원
      ⏱️ 평균 판매 기간: 3일
      📉 시장 트렌드: 하락세

      💡 추천: 현재 시세보다 5-10% 낮게 책정하면 빠른 판매 가능합니다.

      [내 매물 가격 조정] [끌어올리기]
```

---

## 11. 성공 지표

### 데모 평가 기준
1. **기능 완성도**: 5가지 Intent 모두 정상 작동
2. **사용자 경험**: 3초 이내 응답 + 명확한 피드백
3. **UI 품질**: 좌우 패널 실시간 동기화
4. **프레젠테이션**: 3가지 시나리오 시연 성공

---

## 12. 리스크 & 대응

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|-----------|
| Gemini API 호출 실패 | 높음 | Retry 로직 + Fallback 규칙 기반 파서 |
| Intent 분류 정확도 낮음 | 중간 | Few-shot 예시 추가 + 프롬프트 튜닝 |
| 대화 컨텍스트 미구현 | 낮음 | "ID 3번 매물"처럼 명시적 지칭 유도 |
| 끌올 제한 미작동 | 낮음 | DB 쿼리로 24시간 체크 로직 추가 |

---

## 13. 폴더 구조 (예상)

```
jol/
├── backend/
│   ├── main.py              # FastAPI 앱
│   ├── database.py          # SQLite 연결 & 스키마
│   ├── models.py            # Pydantic 모델
│   ├── agent.py             # LLM Agent 로직
│   ├── tools.py             # Tool 함수들
│   ├── prompts.py           # System Prompt 템플릿
│   └── config.py            # Gemini API 키 등
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/
│   └── jol.db               # SQLite 파일
├── requirements.txt
└── README.md
```

---

## 14. 다음 단계

1. ✅ PRD 검토 및 승인
2. [ ] 개발 환경 설정 (Python, FastAPI, Gemini API 키)
3. [ ] DB 스키마 생성 & 샘플 데이터 삽입
4. [ ] LLM Agent 프롬프트 작성 & 테스트
5. [ ] Tool 함수 구현
6. [ ] API 엔드포인트 구현
7. [ ] UI 개발
8. [ ] 통합 테스트
9. [ ] 데모 시나리오 시연 준비

---

**작성일**: 2025-10-26
**작성자**: AI Assistant
**버전**: 1.0
