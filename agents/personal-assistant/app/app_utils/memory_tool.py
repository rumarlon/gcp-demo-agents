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
from google.adk.tools.load_memory_tool import LoadMemoryTool
from google.adk.tools.preload_memory_tool import PreloadMemoryTool, _memory_entry_utils

logger = logging.getLogger(__name__)


class CachedPreloadMemoryTool(PreloadMemoryTool):
    """Preloads user memories from Memory Bank and caches the preloaded system instruction

    per session. This guarantees that system instructions remain 100% static across
    consecutive turns within a session, preserving Gemini Context Cache alignment and
    preventing cache miss latency warnings.
    """

    @override
    async def process_llm_request(
        self,
        *,
        tool_context: ToolContext,
        llm_request: LlmRequest,
    ) -> None:
        session = tool_context.session
        session_state = session.state if session else None

        if session_state is not None and "cached_memory_instruction" in session_state:
            cached_si = session_state.get("cached_memory_instruction")
            if cached_si:
                llm_request.append_instructions([cached_si])
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
            if session_state is not None:
                session_state["cached_memory_instruction"] = ""
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
            if session_state is not None:
                session_state["cached_memory_instruction"] = ""
            return

        full_memory_text = "\n".join(memory_text_lines)
        si = f"""The following content is from your previous conversations with the user.
They may be useful for answering the user's current query.
<PAST_CONVERSATIONS>
{full_memory_text}
</PAST_CONVERSATIONS>
"""
        if session_state is not None:
            session_state["cached_memory_instruction"] = si

        llm_request.append_instructions([si])


__all__ = ["CachedPreloadMemoryTool", "LoadMemoryTool"]
