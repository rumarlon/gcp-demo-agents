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

import json
import logging
from unittest.mock import MagicMock

import pytest

from app.app_utils.observability_plugin import (
    IntentOutcomeObservabilityPlugin,
    track_tool_intent_outcome,
)


@pytest.mark.asyncio
async def test_before_model_callback_intent_logging(caplog):
    """Verifies before_model_callback logs structured agent_intent payload."""
    plugin = IntentOutcomeObservabilityPlugin()
    caplog.set_level(logging.INFO)

    # Mock llm_request with user message
    mock_part = MagicMock()
    mock_part.text = "What is the weather in Tokyo?"

    mock_content = MagicMock()
    mock_content.role = "user"
    mock_content.parts = [mock_part]

    mock_request = MagicMock()
    mock_request.contents = [mock_content]

    mock_context = MagicMock()
    mock_context.session_id = "test_session_123"

    mock_agent = MagicMock()
    mock_agent.name = "test_agent"

    await plugin.before_model_callback(
        agent=mock_agent,
        callback_context=mock_context,
        llm_request=mock_request,
    )

    # Verify log output contains agent_intent
    assert any("AGENT INTENT:" in record.message for record in caplog.records)
    log_record = next(r for r in caplog.records if "AGENT INTENT:" in r.message)
    json_str = log_record.message.split("AGENT INTENT: ")[1]
    payload = json.loads(json_str)

    assert payload["event_type"] == "agent_intent"
    assert payload["agent_name"] == "test_agent"
    assert payload["session_id"] == "test_session_123"
    assert "Tokyo" in payload["user_query"]


@pytest.mark.asyncio
async def test_after_model_callback_outcome_logging(caplog):
    """Verifies after_model_callback logs structured agent_outcome payload."""
    plugin = IntentOutcomeObservabilityPlugin()
    caplog.set_level(logging.INFO)

    mock_response = MagicMock()
    mock_response.text = "It's 68 degrees and clear in Tokyo."

    mock_context = MagicMock()
    mock_context.session_id = "test_session_123"
    mock_context._intent_start_time = 1000.0  # mock timestamp

    mock_agent = MagicMock()
    mock_agent.name = "test_agent"

    await plugin.after_model_callback(
        agent=mock_agent,
        callback_context=mock_context,
        llm_response=mock_response,
    )

    assert any("AGENT OUTCOME:" in record.message for record in caplog.records)
    log_record = next(r for r in caplog.records if "AGENT OUTCOME:" in r.message)
    json_str = log_record.message.split("AGENT OUTCOME: ")[1]
    payload = json.loads(json_str)

    assert payload["event_type"] == "agent_outcome"
    assert payload["agent_name"] == "test_agent"
    assert payload["status"] == "success"
    assert "Tokyo" in payload["response_summary"]


def test_track_tool_intent_outcome_decorator(caplog):
    """Verifies tool decorator logs tool_intent and tool_outcome structured payloads."""
    caplog.set_level(logging.INFO)

    @track_tool_intent_outcome
    def dummy_tool(city: str) -> dict:
        return {"status": "success", "city": city}

    res = dummy_tool(city="London")
    assert res["status"] == "success"

    # Check intent log
    assert any("TOOL INTENT:" in record.message for record in caplog.records)
    intent_record = next(r for r in caplog.records if "TOOL INTENT:" in r.message)
    intent_payload = json.loads(intent_record.message.split("TOOL INTENT: ")[1])
    assert intent_payload["event_type"] == "tool_intent"
    assert intent_payload["tool_name"] == "dummy_tool"
    assert intent_payload["arguments"]["city"] == "London"

    # Check outcome log
    assert any("TOOL OUTCOME:" in record.message for record in caplog.records)
    outcome_record = next(r for r in caplog.records if "TOOL OUTCOME:" in r.message)
    outcome_payload = json.loads(outcome_record.message.split("TOOL OUTCOME: ")[1])
    assert outcome_payload["event_type"] == "tool_outcome"
    assert outcome_payload["tool_name"] == "dummy_tool"
    assert outcome_payload["status"] == "success"
    assert "latency_ms" in outcome_payload
