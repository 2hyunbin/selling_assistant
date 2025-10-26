# 🚀 JOL AI Agent - Quick Start Guide

졸업 프로젝트 데모: 중고거래 AI 어시스턴트 챗봇

---

## 📋 사전 준비

### 1. Gemini API 키 발급
1. https://aistudio.google.com/app/apikey 접속
2. "Create API key" 클릭하여 키 발급
3. 키 복사

### 2. API 키 설정
`backend/config.py` 파일 6번째 줄 수정:
```python
GEMINI_API_KEY = "여기에_실제_API_키_붙여넣기"
```

---

## 🎯 실행 방법

### Step 1: 의존성 설치 (최초 1회만)
```bash
cd /Users/vinci/Project/jol
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: 데이터베이스 초기화 (최초 1회만)
```bash
cd backend
source ../venv/bin/activate
python init_db.py
```

실행 결과:
```
🔧 Initializing database...
✅ Database schema created
📦 Inserting 10 sample listings...
🎉 Database initialization complete!
```

### Step 3: 서버 실행
```bash
cd backend
source ../venv/bin/activate
python main.py
```

서버가 실행되면 다음과 같은 화면이 표시됩니다:
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║       JOL - 중고거래 AI 어시스턴트 챗봇                  ║
║                                                          ║
║       Server: http://0.0.0.0:8000                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: 브라우저 접속
```
http://localhost:8000
```

---

## 🎮 데모 시나리오

### 시나리오 1: 매물 조회
```
"어제 올린 물건 보여줘"
"전자기기 카테고리 매물 알려줘"
```

### 시나리오 2: 가격 조정
```
"맥북 가격 10% 낮춰줘"
"ID 2번 매물 5만원 인하해줘"
```

### 시나리오 3: 끌어올리기
```
"가장 오래된 매물 끌어올려줘"
"ID 3번 매물 끌올"
```

### 시나리오 4: 글 수정
```
"맥북 제목을 더 매력적으로 바꿔줘"
"ID 4번 매물 제목 수정"
```

### 시나리오 5: 시장 인사이트
```
"전자기기 시세 알려줘"
"강남구 가구 평균 가격은?"
```

---

## 📊 프로젝트 구조

```
jol/
├── backend/              # FastAPI 백엔드
│   ├── main.py          # FastAPI 서버 (엔드포인트)
│   ├── agent.py         # LLM Agent (Gemini API)
│   ├── tools.py         # 5가지 Tool 함수
│   ├── database.py      # SQLite 래퍼
│   ├── models.py        # Pydantic 모델
│   ├── prompts.py       # System Prompt
│   ├── config.py        # 설정 (API 키)
│   ├── init_db.py       # DB 초기화
│   ├── test_tools.py    # Tool 테스트
│   ├── test_agent.py    # Agent 테스트
│   └── test_api.py      # API 테스트
├── frontend/             # Vanilla JS UI
│   ├── index.html       # 메인 HTML
│   ├── style.css        # 스타일
│   └── app.js           # JavaScript
├── data/
│   └── jol.db           # SQLite 데이터베이스
├── venv/                # Python 가상환경
├── requirements.txt     # 의존성 목록
├── README.md
├── PRD.md               # 상세 요구사항 문서
└── QUICK_START.md       # 이 파일
```

---

## 🔧 트러블슈팅

### 문제: "GEMINI_API_KEY not set"
**해결**: `backend/config.py` 파일에서 API 키 설정 확인

### 문제: 포트 8000이 이미 사용 중
**해결**:
```bash
# 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9

# 또는 config.py에서 포트 변경
PORT = 8001
```

### 문제: 프론트엔드가 로드되지 않음
**해결**:
1. 서버가 실행 중인지 확인 (`http://localhost:8000/health`)
2. 브라우저 콘솔 확인 (F12)
3. CORS 에러 시 → `backend/config.py`의 `CORS_ORIGINS` 확인

### 문제: Agent 응답이 느림
**해결**:
- Gemini 1.5 Flash 모델 사용 중 (이미 설정됨)
- 네트워크 연결 확인
- Gemini API 할당량 확인

---

## 📝 주요 기능

### ✅ 구현 완료
- [x] Intent 분류 (6가지)
- [x] Tool 실행 (5가지)
- [x] 가격 조정 (DB 업데이트)
- [x] 끌어올리기 (24시간 제한)
- [x] 제목/내용 수정
- [x] 시장 인사이트 (고정값)
- [x] 실시간 UI 업데이트
- [x] 추천 액션 버튼

### 🎯 핵심 기술
- **LLM**: Google Gemini API (Structured Output)
- **Backend**: FastAPI + SQLite
- **Frontend**: Vanilla JavaScript
- **Agent**: Intent 분류 → Tool 선택 → 실행

---

## 🎓 졸업 프로젝트 발표 팁

### 데모 순서 추천
1. **소개**: "자연어로 중고거래 매물을 관리하는 AI 에이전트"
2. **시나리오 1**: "어제 올린 물건 보여줘" → 조회 기능
3. **시나리오 2**: "맥북 가격 10% 낮춰줘" → 우측 패널에서 실시간 가격 변경 확인
4. **시나리오 3**: "전자기기 시세 알려줘" → 인사이트 제공
5. **강조 포인트**:
   - Gemini API Structured Output 활용
   - 좌우 패널 실시간 동기화
   - 자연어 처리 정확도

### 차별화 포인트
- ✨ **Structured Output**: Pydantic 모델로 안정적인 JSON 응답
- ✨ **Tool Chaining**: "어제 올린 물건 가격 낮춰줘" → 자동으로 조회 후 가격 조정
- ✨ **실시간 UI**: 매물 변경 시 하이라이트 애니메이션
- ✨ **추천 액션**: AI가 다음 액션 제안

---

## 📞 문의

프로젝트 관련 문의: GitHub Issues
API 문서: `http://localhost:8000/docs` (서버 실행 후)

---

**버전**: 1.0.0
**날짜**: 2025-10-26
**작성자**: Vinci
