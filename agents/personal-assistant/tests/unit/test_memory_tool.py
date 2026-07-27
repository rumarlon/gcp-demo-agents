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

from unittest.mock import AsyncMock, MagicMock
import pytest
from google.adk.models import LlmRequest
from google.genai import types

from app.app_utils.memory_tool import CachedPreloadMemoryTool


@pytest.mark.asyncio
async def test_cached_preload_memory_tool_skips_tool_response_turn() -> None:
    tool = CachedPreloadMemoryTool()

    tool_context = MagicMock()
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text="What is the weather?")],
    )
    tool_context.user_content = user_content
    tool_context.search_memory = AsyncMock()

    # LlmRequest ending with a function_response turn
    llm_request = LlmRequest()
    llm_request.contents = [
        types.Content(
            role="user", parts=[types.Part.from_text(text="What is the weather?")]
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_function_call(name="get_weather", args={"query": "NYC"})
            ],
        ),
        types.Content(
            role="user",
            parts=[
                types.Part.from_function_response(
                    name="get_weather", response={"result": "75 degrees"}
                )
            ],
        ),
    ]

    await tool.process_llm_request(tool_context=tool_context, llm_request=llm_request)

    # Search memory should not be called and function_response turn must be left untouched
    tool_context.search_memory.assert_not_called()
    assert len(llm_request.contents[-1].parts) == 1
    assert llm_request.contents[-1].parts[0].function_response is not None


@pytest.mark.asyncio
async def test_cached_preload_memory_tool_attaches_memory_to_user_turn() -> None:
    tool = CachedPreloadMemoryTool()

    tool_context = MagicMock()
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Hello")],
    )
    tool_context.user_content = user_content

    mock_memory = MagicMock()
    mock_memory.timestamp = "2026-07-26"
    mock_memory.author = "user"
    mock_memory.fact = "User lives in New York"

    mock_search_response = MagicMock()
    mock_search_response.memories = [mock_memory]

    tool_context.search_memory = AsyncMock(return_value=mock_search_response)

    llm_request = LlmRequest()
    llm_request.contents = [
        types.Content(role="user", parts=[types.Part.from_text(text="Hello")]),
    ]

    await tool.process_llm_request(tool_context=tool_context, llm_request=llm_request)

    tool_context.search_memory.assert_called_once_with("Hello")
    assert len(llm_request.contents[-1].parts) == 2
    assert "<PAST_CONVERSATIONS>" in llm_request.contents[-1].parts[1].text
