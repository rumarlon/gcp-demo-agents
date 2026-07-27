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

import datetime
import logging
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.app_utils.memory_tool import CachedPreloadMemoryTool
from app.app_utils.model_armor_plugin import ModelArmorPlugin
from app.app_utils.observability_plugin import IntentOutcomeObservabilityPlugin
from app.app_utils.tools import get_current_time, get_weather

logger = logging.getLogger(__name__)

MODEL = "gemini-3.6-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends session events to Memory Bank for long-term memory extraction and generation."""
    try:
        await callback_context.add_session_to_memory()
    except ValueError as e:
        logger.warning("Memory service not active for session: %s", e)
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        client_kwargs={"location": "global"},
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "- WARM & ENGAGING TONE: Maintain a polite, enthusiastic, personable, and helpful persona at all times.\n"
        "- ACKNOWLEDGE INTRODUCTIONS & STATEMENTS: When the user introduces themselves (e.g., 'My name is Marlon', 'I'm Alex'), shares personal details, or updates preferences, ALWAYS acknowledge them immediately with a warm greeting and confirmation (e.g., 'Nice to meet you, Marlon! I've noted that down. How can I help you today?').\n\n"
        "TOOL USAGE GUIDELINES:\n"
        "- Only invoke weather or time tools when the user explicitly requests weather or current time information.\n"
        "- For casual statements, general conversation, or greetings, respond conversationally without calling weather or time tools.\n"
        "- ERROR RECOVERY: If a tool returns a response with status 'error', inspect the provided 'suggestion' field and follow its guidance to politely ask the user for clarification or offer supported options.\n\n"
        "RULES FOR USING MEMORIES:\n"
        "- PERSONALIZED GREETINGS: When the user greets you (e.g., 'hello', 'hi', 'good morning', 'hey'), "
        "check the <PAST_CONVERSATIONS> memory context or current conversation. If you know the user's name or preferred name, "
        "ALWAYS address the user warmly by name in your greeting (e.g., 'Hello Marlon!', 'Hi Marlon! How can I assist you today?').\n"
        "- PREFERENCES & CONTEXT: Automatically apply stored user preferences (coffee preferences, diet, "
        "favorite activities, home city) to answer questions without asking the user to repeat themselves.\n"
        "- NATURAL CONVERSATION: Integrate memories seamlessly without saying 'According to my memories'.\n"
        "- UPDATES: Gracefully accept new or updated user preferences."
    ),
    tools=[
        get_weather,
        get_current_time,
        CachedPreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
    plugins=[
        ModelArmorPlugin(),
        IntentOutcomeObservabilityPlugin(),
    ],
)
