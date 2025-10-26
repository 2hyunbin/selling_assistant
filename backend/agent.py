"""
LLM Agent using Gemini API with structured output
"""
import json
from typing import List, Dict, Any, Optional
from typing_extensions import Annotated
from enum import Enum
from pydantic import BaseModel, Field

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import GEMINI_API_KEY, GEMINI_MODEL
from prompts import get_system_prompt, get_user_prompt_template
from tools import execute_tool
from database import db


# === Pydantic Models for Structured Output ===

class IntentType(str, Enum):
    """Intent classification"""
    QUERY_LISTINGS = "QUERY_LISTINGS"
    ADJUST_PRICE = "ADJUST_PRICE"
    BOOST_LISTING = "BOOST_LISTING"
    UPDATE_CONTENT = "UPDATE_CONTENT"
    GET_INSIGHTS = "GET_INSIGHTS"
    GENERAL_CHAT = "GENERAL_CHAT"


class ToolCall(BaseModel):
    """Single tool call with parameters"""
    name: str = Field(description="Tool function name")
    params: Dict[str, Any] = Field(description="Tool parameters as key-value pairs")


class SuggestedAction(BaseModel):
    """Suggested action button for user"""
    label: str = Field(description="Button label shown to user")
    action: str = Field(description="Tool name to execute")
    params: Dict[str, Any] = Field(description="Tool parameters")


class AgentPlan(BaseModel):
    """Agent's analysis and execution plan"""
    intent: IntentType = Field(description="Classified user intent")
    reasoning: str = Field(description="Why this intent and these tools were chosen")
    tools_to_execute: List[ToolCall] = Field(
        description="List of tools to execute in order. If user mentions 'yesterday's item' without ID, first use query_listings, then use that result's ID for next action."
    )
    response_text: str = Field(
        description="Friendly response text to show user after executing tools"
    )
    suggested_actions: List[SuggestedAction] = []


# === Agent Class ===

class GeminiAgent:
    """LLM Agent for listing management"""

    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        """Initialize Gemini agent"""
        genai.configure(api_key=api_key)
        self.model_name = model_name

        # Safety settings (permissive for demo)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

    async def get_listings_summary(self) -> str:
        """Get summary of current listings for context"""
        try:
            listings = await db.get_all_listings()
            if not listings:
                return "현재 판매중인 매물이 없습니다."

            summary_lines = []
            for listing in listings[:10]:  # Show max 10 items
                summary_lines.append(
                    f"- ID {listing['id']}: {listing['title']} "
                    f"({listing['price']:,}원, {listing['category']}, "
                    f"{listing['region']}, {listing['created_at'][:10]} 등록)"
                )

            return "\n".join(summary_lines)
        except Exception as e:
            return f"매물 조회 실패: {str(e)}"

    async def plan_action(self, user_message: str) -> AgentPlan:
        """
        Analyze user message and create execution plan using structured output

        Args:
            user_message: User's natural language request

        Returns:
            AgentPlan object with intent, tools, and response
        """
        # Get context
        listings_summary = await self.get_listings_summary()

        # Build prompts
        system_prompt = get_system_prompt(listings_summary)
        user_prompt = get_user_prompt_template(user_message)

        # Configure model for JSON output
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            safety_settings=self.safety_settings,
            generation_config={
                "response_mime_type": "application/json",
            }
        )

        try:
            # Generate JSON response
            response = model.generate_content(user_prompt)

            # Parse JSON output
            plan: AgentPlan = AgentPlan.model_validate_json(response.text)

            return plan

        except Exception as e:
            # Fallback plan for errors
            print(f"Agent planning error: {e}")
            return AgentPlan(
                intent=IntentType.GENERAL_CHAT,
                reasoning=f"에러 발생: {str(e)}",
                tools_to_execute=[],
                response_text=f"죄송합니다. 요청을 처리하는 중 오류가 발생했습니다: {str(e)}",
                suggested_actions=[]
            )

    async def execute_plan(self, plan: AgentPlan) -> Dict[str, Any]:
        """
        Execute the planned tools

        Args:
            plan: AgentPlan from plan_action

        Returns:
            {
                "success": bool,
                "results": List[Dict],
                "executed_tools": List[str],
                "updated_listings": List[int]
            }
        """
        results = []
        executed_tools = []
        updated_listings = set()

        for tool_call in plan.tools_to_execute:
            try:
                # Execute tool
                result = await execute_tool(tool_call.name, tool_call.params)
                results.append({
                    "tool": tool_call.name,
                    "params": tool_call.params,
                    "result": result
                })
                executed_tools.append(tool_call.name)

                # Track updated listings
                if result.get("success") and result.get("listing_id"):
                    updated_listings.add(result["listing_id"])

                # For query_listings, if next tool needs listing_id, inject it
                if tool_call.name == "query_listings" and result.get("success"):
                    listings = result.get("listings", [])
                    if listings and len(plan.tools_to_execute) > 1:
                        # Get first listing ID for next tool
                        first_listing_id = listings[0]["id"]
                        # Inject into next tool's params if it needs listing_id
                        next_idx = plan.tools_to_execute.index(tool_call) + 1
                        if next_idx < len(plan.tools_to_execute):
                            next_tool = plan.tools_to_execute[next_idx]
                            if "listing_id" in next_tool.params and next_tool.params["listing_id"] is None:
                                next_tool.params["listing_id"] = first_listing_id

            except Exception as e:
                results.append({
                    "tool": tool_call.name,
                    "params": tool_call.params,
                    "result": {
                        "success": False,
                        "message": f"Tool 실행 오류: {str(e)}"
                    }
                })

        return {
            "success": len(results) > 0,
            "results": results,
            "executed_tools": executed_tools,
            "updated_listings": list(updated_listings)
        }

    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Main entry point: Process user message end-to-end

        Args:
            user_message: User's natural language request

        Returns:
            {
                "intent": str,
                "response": str,
                "reasoning": str,
                "actions_taken": List[Dict],
                "suggested_actions": List[Dict],
                "updated_listings": List[int]
            }
        """
        # Step 1: Plan action
        plan = await self.plan_action(user_message)

        # Step 2: Execute tools
        execution_result = await self.execute_plan(plan)

        # Step 3: Build final response
        return {
            "intent": plan.intent.value,
            "response": plan.response_text,
            "reasoning": plan.reasoning,
            "actions_taken": execution_result["results"],
            "suggested_actions": [action.model_dump() for action in plan.suggested_actions],
            "updated_listings": execution_result["updated_listings"]
        }


# Global agent instance
agent = GeminiAgent()
