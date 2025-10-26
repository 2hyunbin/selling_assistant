"""
Configuration file for the JOL (중고거래) AI Agent
"""
import os
from pathlib import Path

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyAlj_zO6KXM_RKuy2GN0m6VhqEuD4Bk7nQ"
GEMINI_MODEL = "gemini-2.5-flash"

# Database Configuration
# Use absolute path to avoid confusion
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = str(BASE_DIR / "data" / "jol.db")

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True  # Set to Falㅂse in production

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://0.0.0.0:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]

# Business Rules
BOOST_COOLDOWN_HOURS = 24  # 끌어올리기 쿨다운 시간
RECOMMENDED_DISCOUNT_PERCENT = 10  # 권장 할인율

# Market Insights Data (고정값)
INSIGHTS_DATA = {
    ("전자기기", "강남구"): {
        "average_price": 850000,
        "avg_sell_days": 3,
        "trend": "하락세",
        "sample_count": 42,
        "recommendation": "현재 시세보다 5-10% 낮게 책정 추천"
    },
    ("전자기기", "서초구"): {
        "average_price": 780000,
        "avg_sell_days": 4,
        "trend": "보합",
        "sample_count": 38,
        "recommendation": "적정 가격대입니다. 제목 개선을 권장합니다"
    },
    ("가구", "강남구"): {
        "average_price": 320000,
        "avg_sell_days": 7,
        "trend": "상승세",
        "sample_count": 25,
        "recommendation": "수요가 증가하고 있습니다. 현재 가격 유지 추천"
    },
    ("가구", "서초구"): {
        "average_price": 290000,
        "avg_sell_days": 8,
        "trend": "보합",
        "sample_count": 21,
        "recommendation": "평균 거래 기간이 길어 끌어올리기 권장"
    },
    ("의류", "강남구"): {
        "average_price": 45000,
        "avg_sell_days": 2,
        "trend": "하락세",
        "sample_count": 67,
        "recommendation": "빠른 판매를 위해 가격 인하 권장"
    },
    ("의류", "서초구"): {
        "average_price": 42000,
        "avg_sell_days": 3,
        "trend": "하락세",
        "sample_count": 54,
        "recommendation": "경쟁이 치열합니다. 사진 및 설명 개선 권장"
    },
    ("default", "default"): {
        "average_price": 500000,
        "avg_sell_days": 5,
        "trend": "보합",
        "sample_count": 30,
        "recommendation": "시장 데이터를 수집 중입니다"
    }
}

# Categories and Regions
CATEGORIES = ["전자기기", "가구", "의류", "도서", "스포츠", "기타"]
REGIONS = ["강남구", "서초구", "송파구", "강동구", "기타"]
