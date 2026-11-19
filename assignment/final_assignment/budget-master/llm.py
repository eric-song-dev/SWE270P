# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""OpenAI-compatible LLM client shared by all agents, with built-in usage tracking.

Every LLM request in the system goes through LLMClient.chat(), so counting API
calls and tokens here covers the whole system. Each agent task creates its own
LLMClient, which gives a usage breakdown per agent and per task.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

PROJECT_ROOT = Path(__file__).resolve().parent

# Read LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, ... from the .env file next to this module.
load_dotenv(PROJECT_ROOT / ".env")


class UsageTracker:
    """Counts the LLM API calls and tokens consumed by one agent task."""

    def __init__(self):
        """Starts all counters at zero."""
        self.api_calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0

    def record(self, usage):
        """Adds one API call plus the token counts from the `usage` field of its response.

        `usage` may be None when a provider does not report tokens; the call is still counted.
        """
        self.api_calls += 1
        if usage is not None:
            self.prompt_tokens += usage.prompt_tokens or 0
            self.completion_tokens += usage.completion_tokens or 0
            self.total_tokens += usage.total_tokens or 0

    def as_dict(self):
        """Returns the counters as a JSON-serializable dict (sent back to the orchestrator over MCP)."""
        return {
            "api_calls": self.api_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


class LLMClient:
    """Thin wrapper around the OpenAI chat-completions API that records usage for every call."""

    def __init__(self):
        """Creates the API client from the LLM_* environment variables (defaults target DeepSeek)."""
        self.model = os.getenv("LLM_MODEL", "deepseek-flash")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "16384"))
        self.thinking = os.getenv("LLM_THINKING", "")
        self.client = AsyncOpenAI(
            api_key=os.getenv("LLM_API_KEY") or "missing-api-key",
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        )
        self.usage = UsageTracker()

    async def chat(self, messages, tools=None):
        """Sends one chat-completion request and returns the assistant message.

        Parameters:
            messages (list[dict]): The conversation so far in OpenAI chat format.
            tools (list[dict] | None): Tool definitions in OpenAI function-calling format.

        The token usage reported by the API is added to self.usage before returning.
        """
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        if tools:
            params["tools"] = tools
        if self.thinking:
            # DeepSeek-specific switch ("enabled" / "disabled"); only sent when configured.
            params["extra_body"] = {"thinking": {"type": self.thinking}}
        response = await self.client.chat.completions.create(**params)
        self.usage.record(response.usage)
        return response.choices[0].message
