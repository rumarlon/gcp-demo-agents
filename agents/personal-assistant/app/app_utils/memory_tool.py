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

import logging
from typing import override

from google.adk.models import LlmRequest
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool, _memory_entry_utils
from google.genai import types

logger = logging.getLogger(__name__)


class CachedPreloadMemoryTool(PreloadMemoryTool):
    """Preloads user memories from Memory Bank and attaches them to user turn content.

    By attaching memory context to `llm_request.contents` (the user's turn) rather than
    mutating `system_instruction` via `append_instructions`, the top-level system instruction
    remains 100% static and immutable across consecutive session turns. This preserves Gemini
    Context Cache alignment, completely eliminating cache miss performance warnings and lowering
    response generation latency.
    """

    @override
    async def process_llm_request(
        self,
        *,
        tool_context: ToolContext,
        llm_request: LlmRequest,
    ) -> None:
        if not llm_request.contents:
            return

        last_content = llm_request.contents[-1]
        if last_content.role != "user" or not last_content.parts:
            return

        # Do NOT attach memory on tool execution turns (which contain function_response or function_call)
        if any(p.function_response or p.function_call for p in last_content.parts):
            return

        # Do NOT attach duplicate memory if already injected into this turn
        if any(p.text and "<PAST_CONVERSATIONS>" in p.text for p in last_content.parts):
            return

        user_content = tool_context.user_content
        if not user_content or not user_content.parts or not user_content.parts[0].text:
            return

        user_query: str = user_content.parts[0].text
        try:
            response = await tool_context.search_memory(user_query)
        except Exception:
            logger.warning("Failed to preload memory for query: %s", user_query)
            return

        if not response or not response.memories:
            return

        memory_text_lines = []
        for memory in response.memories:
            if time_str := (f"Time: {memory.timestamp}" if memory.timestamp else ""):
                memory_text_lines.append(time_str)
            if memory_text := _memory_entry_utils.extract_text(memory):
                memory_text_lines.append(
                    f"{memory.author}: {memory_text}" if memory.author else memory_text
                )

        if not memory_text_lines:
            return

        full_memory_text = "\n".join(memory_text_lines)
        memory_part = types.Part.from_text(
            text=f"\n\n<PAST_CONVERSATIONS>\n{full_memory_text}\n</PAST_CONVERSATIONS>"
        )

        last_content.parts.append(memory_part)


__all__ = ["CachedPreloadMemoryTool"]
