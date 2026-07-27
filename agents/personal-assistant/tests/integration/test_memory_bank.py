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

from dotenv import load_dotenv

load_dotenv()

import pytest
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


@pytest.mark.asyncio
async def test_memory_bank_integration():
    """Verifies memory service integration, session memory addition, and memory search capabilities."""
    memory_service = InMemoryMemoryService()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
        memory_service=memory_service,
    )

    user_id = "test_user_42"

    # Step 1: Create Session 1
    session1 = await session_service.create_session(app_name="app", user_id=user_id)

    # Step 2: Send user message containing a specific preference
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="I love matcha tea and dark chocolate.")],
    )

    response_events = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session1.id,
        new_message=message,
    ):
        response_events.append(event)

    assert len(response_events) > 0

    # Step 3: Explicitly sync session to memory bank service
    session1 = await session_service.get_session(
        app_name="app", user_id=user_id, session_id=session1.id
    )
    await memory_service.add_session_to_memory(session1)

    # Step 4: Search memory bank for user preferences
    search_results = await memory_service.search_memory(
        app_name="app",
        user_id=user_id,
        query="tea preference",
    )

    assert search_results is not None


@pytest.mark.asyncio
async def test_agent_tool_execution():
    """Verifies that the root_agent correctly responds to basic tools."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
    )

    user_id = "test_user_1"
    session = await session_service.create_session(app_name="app", user_id=user_id)

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="What's the weather in San Francisco?")],
    )

    response_texts = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_texts.append(part.text)

    full_response = " ".join(response_texts)
    assert len(full_response) > 0


@pytest.mark.asyncio
async def test_personalized_greeting_from_memory():
    """Verifies that the agent uses stored memory of the user's name when greeting them in a new session."""
    memory_service = InMemoryMemoryService()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
        memory_service=memory_service,
    )

    user_id = "marlon_user_123"

    # Session 1: User introduces themselves
    session1 = await session_service.create_session(app_name="app", user_id=user_id)
    msg1 = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="Hello, my name is Marlon and I live in San Francisco."
            )
        ],
    )
    async for _ in runner.run_async(
        user_id=user_id, session_id=session1.id, new_message=msg1
    ):
        pass

    # Fetch updated session containing recorded events from session_service
    session1 = await session_service.get_session(
        app_name="app", user_id=user_id, session_id=session1.id
    )
    await memory_service.add_session_to_memory(session1)

    # Session 2: New session, user says 'Hello!'
    session2 = await session_service.create_session(app_name="app", user_id=user_id)
    msg2 = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Hello!")],
    )

    response_texts = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session2.id, new_message=msg2
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_texts.append(part.text)

    full_response = " ".join(response_texts)
    assert "marlon" in full_response.lower()


@pytest.mark.asyncio
async def test_cross_session_preference_recall():
    """Verifies that user preferences stored in memory are applied to queries in subsequent sessions."""
    memory_service = InMemoryMemoryService()
    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name="app",
        session_service=session_service,
        memory_service=memory_service,
    )

    user_id = "coffee_lover_99"

    # Session 1: Storing coffee preference
    session1 = await session_service.create_session(app_name="app", user_id=user_id)
    msg1 = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="My absolute favorite coffee is an oat milk latte."
            )
        ],
    )
    async for _ in runner.run_async(
        user_id=user_id, session_id=session1.id, new_message=msg1
    ):
        pass

    session1 = await session_service.get_session(
        app_name="app", user_id=user_id, session_id=session1.id
    )
    await memory_service.add_session_to_memory(session1)

    # Session 2: Open-ended coffee question
    session2 = await session_service.create_session(app_name="app", user_id=user_id)
    msg2 = types.Content(
        role="user",
        parts=[types.Part.from_text(text="What coffee should I order today?")],
    )

    response_texts = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session2.id, new_message=msg2
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_texts.append(part.text)

    full_response = " ".join(response_texts)
    assert "oat milk" in full_response.lower() or "latte" in full_response.lower()
