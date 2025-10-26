"""
LLM Agent using Gemini API Function Calling
Completely rewritten to use native function calling
"""
from typing import Dict, Any
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.protobuf.json_format import MessageToDict

from config import GEMINI_API_KEY, GEMINI_MODEL
from database import db
from tools import (
    query_listings,
    adjust_price,
    boost_listing,
    update_content,
    get_market_insights
)


class GeminiAgent:
    """LLM Agent using Function Calling"""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        """Initialize Gemini agent with function calling"""
        genai.configure(api_key=api_key)
        self.model_name = model_name

        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # Register tools as function declarations
        self.tools = [
            self._create_function_declaration(
                "query_listings",
                "매물을 조회합니다. 시간, 카테고리, 지역으로 필터링하고 다양한 기준으로 정렬할 수 있습니다.",
                {
                    "days_ago": {
                        "type": "INTEGER",
                        "description": "최근 N일 범위로 조회 (N일 전부터 지금까지). 예: 3=최근3일, 10=최근10일, 30=최근30일. exact_day_ago와 동시 사용 불가"
                    },
                    "exact_day_ago": {
                        "type": "INTEGER",
                        "description": "특정일 당일만 조회 (정확히 N일 전). 예: 0=오늘만, 1=어제만, 2=그저께만. days_ago와 동시 사용 불가"
                    },
                    "category": {
                        "type": "STRING",
                        "description": "카테고리 필터 (예: 전자기기, 가구, 의류)"
                    },
                    "region": {
                        "type": "STRING",
                        "description": "지역 필터 (예: 강남구, 서초구)"
                    },
                    "status": {
                        "type": "STRING",
                        "description": "판매 상태 (기본값: active)",
                        "enum": ["active", "sold"]
                    },
                    "sort_by": {
                        "type": "STRING",
                        "description": "정렬 기준 필드 (기본값: created_at)",
                        "enum": ["created_at", "updated_at", "last_boosted_at", "price", "boost_count"]
                    },
                    "sort_order": {
                        "type": "STRING",
                        "description": "정렬 순서 - ASC (오름차순, 오래된/낮은 것부터), DESC (내림차순, 최신/높은 것부터, 기본값)",
                        "enum": ["ASC", "DESC"]
                    }
                }
            ),
            self._create_function_declaration(
                "adjust_price",
                "매물의 가격을 조정합니다.",
                {
                    "listing_id": {
                        "type": "INTEGER",
                        "description": "매물 ID"
                    },
                    "new_price": {
                        "type": "INTEGER",
                        "description": "새로운 가격 (원 단위)"
                    }
                },
                required=["listing_id", "new_price"]
            ),
            self._create_function_declaration(
                "boost_listing",
                "매물을 끌어올립니다. 24시간에 한 번만 가능합니다.",
                {
                    "listing_id": {
                        "type": "INTEGER",
                        "description": "매물 ID"
                    }
                },
                required=["listing_id"]
            ),
            self._create_function_declaration(
                "update_content",
                "매물의 제목이나 내용을 수정합니다.",
                {
                    "listing_id": {
                        "type": "INTEGER",
                        "description": "매물 ID"
                    },
                    "title": {
                        "type": "STRING",
                        "description": "새로운 제목 (선택사항)"
                    },
                    "content": {
                        "type": "STRING",
                        "description": "새로운 내용 (선택사항)"
                    }
                },
                required=["listing_id"]
            ),
            self._create_function_declaration(
                "get_market_insights",
                "카테고리와 지역의 시장 시세 정보를 제공합니다.",
                {
                    "category": {
                        "type": "STRING",
                        "description": "카테고리 (예: 전자기기, 가구, 의류)"
                    },
                    "region": {
                        "type": "STRING",
                        "description": "지역 (예: 강남구, 서초구)"
                    }
                },
                required=["category", "region"]
            )
        ]

        # Map function names to actual functions
        self.function_map = {
            "query_listings": query_listings,
            "adjust_price": adjust_price,
            "boost_listing": boost_listing,
            "update_content": update_content,
            "get_market_insights": get_market_insights
        }

    def _create_function_declaration(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        required: list = None
    ) -> Dict[str, Any]:
        """Create a function declaration for Gemini"""
        return {
            "name": name,
            "description": description,
            "parameters": {
                "type": "OBJECT",  # Gemini uses uppercase
                "properties": parameters,
                "required": required or []
            }
        }

    async def get_system_instruction(self) -> str:
        """Get system instruction with current listings"""
        listings = await db.get_all_listings()

        listings_summary = []
        for listing in listings[:10]:
            listings_summary.append(
                f"- ID {listing['id']}: {listing['title']} "
                f"({listing['price']:,}원, {listing['category']}, "
                f"{listing['region']}, {listing['created_at'][:10]} 등록)"
            )

        return f"""당신은 중고거래 플랫폼의 AI 판매 어시스턴트입니다.

[역할]
- 사용자의 자연어 요청을 분석하여 적절한 함수를 호출합니다
- 항상 친절하고 명확하게 응답합니다

[사용 가능한 함수들]
1. query_listings: 매물 조회 (날짜/카테고리/지역 필터)
   - days_ago: 최근 N일 **범위** (N일 전부터 지금까지)
   - exact_day_ago: 특정일 **당일만** (정확히 N일 전)
   - 두 파라미터는 동시 사용 불가 (하나만 선택)
2. adjust_price: 가격 조정
3. boost_listing: 끌어올리기 (24시간 1회 제한)
4. update_content: 제목/내용 수정
5. get_market_insights: 시장 시세 조회

[정책]
- 끌어올리기는 하루 1회만 가능합니다
- 가격 인하 시 10% 이상 권장합니다
- 가격은 0원 이하로 설정할 수 없습니다

[현재 매물 목록]
{chr(10).join(listings_summary)}

[중요 - 날짜 필터 사용법]
**특정일 조회 (exact_day_ago 사용):**
- "오늘 올린 물건" → query_listings(exact_day_ago=0)
- "어제 올린 물건" → query_listings(exact_day_ago=1)
- "그저께 올린 물건" → query_listings(exact_day_ago=2)

**범위 조회 (days_ago 사용):**
- "최근 3일" → query_listings(days_ago=3)
- "최근 10일" → query_listings(days_ago=10)
- "최근 한달" → query_listings(days_ago=30)
- "지난 주" → query_listings(days_ago=7)

[가격 조정 워크플로우]
- "어제 올린 물건 가격 낮춰줘" 같은 요청:
  1. 먼저 query_listings(exact_day_ago=1)로 조회
  2. 결과를 확인한 후 adjust_price() 호출
- 가격 조정 시 정확한 계산:
  - "10% 낮춰줘" → 현재가 × 0.9
  - "5만원 낮춰줘" → 현재가 - 50000

[응답 형식 가이드]
응답은 반드시 **Markdown 형식**으로 작성하세요:
- 제목이나 섹션 구분: ## 제목
- 강조: **중요한 내용**
- 리스트: 간결하게 작성
- 숫자: 천 단위 콤마 사용 (예: 35,000원)

**매우 중요 - 매물 조회 응답 규칙**:
매물 조회 시 **절대로** 매물 정보를 텍스트로 나열하지 마세요!

**❌ 절대 금지 - 이렇게 하지 마세요:**
- "1. 유니클로 캐시미어 니트 (35,000원, 의류, 서초구)"
- "ID 8: 유니클로 캐시미어 니트 - 35,000원"
- "아이폰 13 프로 (850,000원, 전자기기, 강남구), IKEA 책상 (120,000원, 가구, 서초구)"
- 매물 제목, 가격, 카테고리, 지역 등을 텍스트로 나열하는 모든 형태

**✅ 올바른 응답 예시:**
- "어제 등록된 매물 **2개**를 찾았습니다."
- "최근 3일간 **5개**의 전자기기 매물이 있습니다."
- "가격을 낮출 매물 **3개**를 찾았습니다."

**이유**: 매물 상세 정보(제목, 가격, 카테고리, 지역)는 UI 카드로 자동 표시됩니다.
응답 텍스트에는 **개수와 간단한 설명만** 포함하세요.
"""

    async def process_message(self, user_message: str, history: list = None) -> Dict[str, Any]:
        """
        Process user message using function calling

        Args:
            user_message: User's natural language request

        Returns:
            Response with function call results
        """
        try:
            # Get system instruction
            system_instruction = await self.get_system_instruction()

            # Create model with function calling
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
                tools=self.tools,
                safety_settings=self.safety_settings
            )

            # Build chat history for context
            chat_history = []
            if history:
                for msg in history:
                    # Convert to Gemini format
                    if msg.get("role") == "user":
                        chat_history.append({
                            "role": "user",
                            "parts": [msg["content"]]
                        })
                    elif msg.get("role") == "assistant":
                        chat_history.append({
                            "role": "model",
                            "parts": [msg["content"]]
                        })

            # Start chat session with history (manual function calling for async support)
            chat = model.start_chat(history=chat_history)

            # Send initial message
            response = chat.send_message(user_message)

            # Collect function call results
            actions_taken = []
            updated_listings = set()
            function_responses = []

            # Process function calls manually (supports async)
            max_iterations = 5  # Prevent infinite loops
            iteration = 0

            while iteration < max_iterations:
                # Check if model wants to call functions
                if not response.candidates:
                    break

                parts = response.candidates[0].content.parts
                function_calls = [p for p in parts if hasattr(p, 'function_call')]

                if not function_calls:
                    # No more function calls, we're done
                    break

                # Execute each function call
                for part in function_calls:
                    fc = part.function_call
                    func_name = fc.name

                    # Convert protobuf Struct to dict
                    if fc.args is None:
                        func_args = {}
                    else:
                        # MessageMapContainer can be iterated directly
                        try:
                            func_args = {k: v for k, v in fc.args.items()}
                        except Exception as e:
                            print(f"Args conversion error: {e}, type: {type(fc.args)}")
                            func_args = {}

                    # 🔍 DEBUG: 함수 호출 로그
                    print(f"🔧 Calling function: {func_name}")
                    print(f"📝 Arguments: {func_args}")

                    # Execute async function
                    if func_name in self.function_map:
                        result = await self.function_map[func_name](**func_args)
                        print(f"✅ Result: {result}")

                        actions_taken.append({
                            "tool": func_name,
                            "result": result
                        })

                        # Track updated listings
                        if result.get("success") and result.get("listing_id"):
                            updated_listings.add(result["listing_id"])

                        # Prepare function response for model
                        function_responses.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=func_name,
                                    response={"result": result}
                                )
                            )
                        )

                # Send function results back to model
                if function_responses:
                    response = chat.send_message(function_responses)
                    function_responses = []

                iteration += 1

            # Get final text response
            final_response = response.text if response.candidates else "처리 완료"

            return {
                "intent": "AUTO_DETECTED",  # Function calling handles this
                "response": final_response,
                "reasoning": "Function calling으로 자동 처리됨",
                "actions_taken": actions_taken,
                "suggested_actions": [],  # 추가: 빈 배열로 초기화
                "updated_listings": list(updated_listings)
            }

        except Exception as e:
            import traceback
            print(f"Agent error: {e}")
            traceback.print_exc()
            return {
                "intent": "ERROR",
                "response": f"죄송합니다. 요청 처리 중 오류가 발생했습니다: {str(e)}",
                "reasoning": f"에러: {str(e)}",
                "actions_taken": [],
                "suggested_actions": [],  # 추가: 빈 배열로 초기화
                "updated_listings": []
            }


# Global agent instance
agent = GeminiAgent()
