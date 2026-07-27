# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import functools
import json
import logging
import os
import time
from typing import Any, Callable, Optional

from google.adk.plugins import BasePlugin

try:
    from opentelemetry import trace

    has_otel = True
except ImportError:
    has_otel = False

logger = logging.getLogger(__name__)

# Configurable log level, defaulting to INFO
LOG_LEVEL_NAME = os.getenv("OBSERVABILITY_LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME, logging.INFO)


def _get_current_span():
    if has_otel:
        try:
            span = trace.get_current_span()
            if span and span.is_recording():
                return span
        except Exception:
            pass
    return None


class IntentOutcomeObservabilityPlugin(BasePlugin):
    """ADK Observability Plugin capturing explicit Intent vs. Outcome logging and trace span attributes.

    Emits structured JSON logs and sets OpenTelemetry span attributes before and after
    agent / LLM model inference turns.
    """

    def __init__(self, name: str = "intent_outcome_observability_plugin"):
        super().__init__(name=name)

    async def before_model_callback(
        self,
        agent: Any = None,
        callback_context: Any = None,
        llm_request: Any = None,
        **kwargs: Any,
    ) -> Optional[Any]:
        """Captures Agent Intent before sending query to LLM."""
        req_obj = llm_request or getattr(callback_context, "llm_request", None)
        agent_name = getattr(agent, "name", "root_agent") if agent else "root_agent"
        session_id = (
            getattr(callback_context, "session_id", None) if callback_context else None
        )

        user_query = ""
        if req_obj and getattr(req_obj, "contents", None):
            last_content = req_obj.contents[-1]
            if getattr(last_content, "role", None) == "user":
                user_text_parts = [
                    part.text
                    for part in getattr(last_content, "parts", [])
                    if hasattr(part, "text") and part.text
                ]
                user_query = " ".join(user_text_parts)

        # Store start time on context for latency calculation
        if callback_context:
            setattr(callback_context, "_intent_start_time", time.time())

        # Log structured Agent Intent
        intent_payload = {
            "event_type": "agent_intent",
            "agent_name": agent_name,
            "session_id": session_id,
            "user_query": user_query[:500],  # Truncate if long
            "timestamp": time.time(),
        }
        logger.log(LOG_LEVEL, f"AGENT INTENT: {json.dumps(intent_payload)}")

        # Record OpenTelemetry trace attributes
        span = _get_current_span()
        if span:
            span.set_attribute("agent.intent.name", agent_name)
            if user_query:
                span.set_attribute("agent.intent.user_query", user_query[:256])

        return None

    async def after_model_callback(
        self,
        agent: Any = None,
        callback_context: Any = None,
        llm_response: Any = None,
        **kwargs: Any,
    ) -> Optional[Any]:
        """Captures Agent Outcome after receiving response from LLM."""
        resp_obj = llm_response or getattr(callback_context, "llm_response", None)
        agent_name = getattr(agent, "name", "root_agent") if agent else "root_agent"
        session_id = (
            getattr(callback_context, "session_id", None) if callback_context else None
        )

        # Calculate latency
        start_time = (
            getattr(callback_context, "_intent_start_time", None)
            if callback_context
            else None
        )
        latency_ms = round((time.time() - start_time) * 1000, 2) if start_time else None

        response_text = getattr(resp_obj, "text", None) if resp_obj else None
        status = "success" if response_text else "empty_or_error"

        outcome_payload = {
            "event_type": "agent_outcome",
            "agent_name": agent_name,
            "session_id": session_id,
            "status": status,
            "latency_ms": latency_ms,
            "response_summary": (
                (response_text[:300] + "...")
                if response_text and len(response_text) > 300
                else response_text
            ),
            "timestamp": time.time(),
        }
        logger.log(LOG_LEVEL, f"AGENT OUTCOME: {json.dumps(outcome_payload)}")

        # Record OpenTelemetry trace attributes
        span = _get_current_span()
        if span:
            span.set_attribute("agent.outcome.status", status)
            if latency_ms is not None:
                span.set_attribute("agent.outcome.latency_ms", latency_ms)

        return None


def track_tool_intent_outcome(func: Callable) -> Callable:
    """Decorator for wrapping tool functions to capture explicit Tool Intent vs. Outcome logging."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__
        start_time = time.time()

        # Log Tool Intent
        intent_payload = {
            "event_type": "tool_intent",
            "tool_name": tool_name,
            "arguments": kwargs or ({"args": args} if args else {}),
            "timestamp": start_time,
        }
        logger.log(LOG_LEVEL, f"TOOL INTENT: {json.dumps(intent_payload)}")

        span = _get_current_span()
        if span:
            span.set_attribute("tool.intent.name", tool_name)

        try:
            result = func(*args, **kwargs)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            status = (
                "error"
                if isinstance(result, dict) and result.get("status") == "error"
                else "success"
            )

            outcome_payload = {
                "event_type": "tool_outcome",
                "tool_name": tool_name,
                "status": status,
                "latency_ms": latency_ms,
                "result_summary": str(result)[:300],
                "timestamp": time.time(),
            }
            logger.log(LOG_LEVEL, f"TOOL OUTCOME: {json.dumps(outcome_payload)}")

            if span:
                span.set_attribute("tool.outcome.status", status)
                span.set_attribute("tool.outcome.latency_ms", latency_ms)

            return result
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            outcome_payload = {
                "event_type": "tool_outcome",
                "tool_name": tool_name,
                "status": "exception",
                "error": str(e),
                "latency_ms": latency_ms,
                "timestamp": time.time(),
            }
            logger.log(
                LOG_LEVEL,
                f"TOOL OUTCOME EXCEPTION: {json.dumps(outcome_payload)}",
            )

            if span:
                span.set_attribute("tool.outcome.status", "exception")
                span.set_attribute("tool.outcome.error", str(e))
            raise

    return wrapper


__all__ = [
    "IntentOutcomeObservabilityPlugin",
    "track_tool_intent_outcome",
]
