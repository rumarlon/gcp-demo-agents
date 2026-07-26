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
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

logger = logging.getLogger(__name__)

MODEL = "gemini-3.6-flash"


def get_weather(query: str) -> str:
    """Simulates getting weather information for a location.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 75 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    elif "tokyo" in query.lower():
        tz_identifier = "Asia/Tokyo"
    elif "london" in query.lower():
        tz_identifier = "Europe/London"
    elif "new york" in query.lower() or "nyc" in query.lower():
        tz_identifier = "America/New_York"
    else:
        tz_identifier = "UTC"

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time in {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}."


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
        "You are a warm, attentive, and highly responsive personalized AI assistant. You remember facts, "
        "preferences, and personal details from past user conversations.\n\n"
        "CORE PERSONALITY & CONVERSATIONAL RULES:\n"
        "- ALWAYS RESPOND WITH TEXT: Every single user turn MUST receive a clear, complete, and friendly verbal response. Never produce empty output or stay silent, even when executing tools or saving memory.\n"
        "- WARM & ENGAGING TONE: Maintain a polite, enthusiastic, personable, and helpful persona at all times.\n"
        "- ACKNOWLEDGE INTRODUCTIONS & STATEMENTS: When the user introduces themselves (e.g., 'My name is Marlon', 'I'm Alex'), shares personal details, or updates preferences, ALWAYS acknowledge them immediately with a warm greeting and confirmation (e.g., 'Nice to meet you, Marlon! I've noted that down. How can I help you today?').\n\n"
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
        PreloadMemoryTool(),
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
