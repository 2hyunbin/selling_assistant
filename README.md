# JOL - 중고거래 AI 에이전트 챗봇

졸업 프로젝트 데모: AI가 자동으로 매물을 관리하는 대화형 에이전트

## 🚀 Quick Start

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Gemini API 키 설정
`backend/config.py` 파일에서 API 키를 설정하세요:
```python
GEMINI_API_KEY = "your_actual_api_key_here"
```

### 3. 서버 실행
```bash
cd backend
python main.py
```

### 4. 브라우저 접속
```
http://localhost:8000
```

## 📁 프로젝트 구조

```
jol/
├── backend/           # FastAPI 백엔드
│   ├── main.py       # FastAPI 앱
│   ├── database.py   # SQLite 연결
│   ├── models.py     # Pydantic 모델
│   ├── agent.py      # LLM Agent 로직
│   ├── tools.py      # Tool 함수들
│   ├── prompts.py    # System Prompt
│   └── config.py     # 설정
├── frontend/          # HTML/CSS/JS UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── data/             # SQLite DB
│   └── jol.db
└── requirements.txt
```

## 🎯 주요 기능

1. **매물 조회**: "어제 올린 물건 보여줘"
2. **가격 조정**: "맥북 가격 10% 낮춰줘"
3. **끌어올리기**: "가장 오래된 매물 끌어올려줘"
4. **글 수정**: "제목을 더 매력적으로 바꿔줘"
5. **시장 인사이트**: "전자기기 시세 알려줘"

## 🛠 기술 스택

- Python 3.13+
- FastAPI
- Google Gemini API
- SQLite
- Vanilla JavaScript

## 📝 개발 단계

- [x] 개발 환경 설정
- [x] DB 스키마 생성
- [x] Tool 함수 구현
- [x] LLM Agent 구현 (Gemini Structured Output)
- [x] API 엔드포인트 구현
- [x] 프론트엔드 UI
- [x] 통합 테스트

---

**Version**: 1.0.0
**Author**: Vinci
**Date**: 2025-10-26
