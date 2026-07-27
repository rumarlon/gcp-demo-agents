# 🎨 Vibe Coding Experience: Replicate `personal-assistant` with `agy` & `agents-cli`

Welcome! This guide is designed for developers who are **new to Google Antigravity (`agy`) and Google Agents CLI (`agents-cli`)**. 

"Vibe Coding" means describing what you want in natural language while your AI pair programmer (**Antigravity**) uses specialized **Agent Development Kit (ADK) skills** to execute the heavy lifting—scaffolding projects, writing clean code, running local tests, and deploying to Google Cloud Platform (GCP).

While `agy` does the coding, this guide explains **exactly what is happening behind the scenes** at every step so you build a deep understanding of Google ADK architecture.

---

## 🧭 Key Concepts for Beginners

| Tool / Concept | What It Is | How It Works Under the Hood |
| :--- | :--- | :--- |
| **`agy` (Antigravity)** | Google's autonomous AI coding assistant. | Reads repository files, invokes CLI commands, delegates to subagents, and applies precision edits via code ASTs. |
| **`agents-cli`** | Google's Agent Development Kit CLI tool. | Standardized tool for project creation (`scaffold`), browser testing (`playground`), evals (`eval`), and cloud deployment (`deploy`). |
| **ADK Runner** | Orchestration engine in `google-adk`. | Manages the loop between user inputs, LLM responses, function tool calls, session storage, and memory retrieval. |
| **Context Caching** | Gemini API optimization feature. | Hashes static parts of the prompt (system instructions) so repeated queries process up to 10x faster and cheaper. |

---

## 🛠️ Step 0: Prerequisites & Initial Environment

1. **Set Up Google Antigravity (`agy`)**:
   Choose one of the following options to run Antigravity:
   - **Option A: Google Antigravity Desktop App / IDE**: Download and open the standalone Antigravity IDE application on your machine.
   - **Option B: Antigravity CLI (`agy`)**: Install and run `agy` directly in your terminal:
     ```bash
     uv tool install agy
     # Or launch agy directly:
     agy
     ```

2. **Install `uv` (Fast Python Package Manager)**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install `google-agents-cli`**:
   ```bash
   uv tool install google-agents-cli
   ```

4. **Authenticate Google Cloud SDK**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

---

## 🚀 Step-by-Step Vibe Coding Workflow

---

### Step 1: Scaffold the ADK Agent Project

**Goal**: Create a clean, production-ready ADK directory structure.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Create a new Google ADK agent project named 'personal-assistant' in the directory 'agents/personal-assistant' using the google-agents-cli-scaffold skill. Configure it for Python 3.12 with uv and set the deployment target to 'agent_runtime'. Include a FastAPI server wrapper and basic project structure.
> ```

#### 🔍 Behind the Scenes (What `agy` and `agents-cli` are doing):
1. **Template Generation**: `agents-cli scaffold create` uses built-in Jinja2 templates to construct a standard ADK layout (`app/`, `tests/`, `pyproject.toml`).
2. **Dependency Resolution**: Configures `pyproject.toml` with `google-adk[gcp]`, `a2a-sdk` (Agent-to-Agent protocol), and `uv` package management.
3. **Deployment Metadata**: Generates `deployment_metadata.json`, which tells GCP tools that this agent targets **Vertex AI Agent Runtime (Reasoning Engine)**.
4. **FastAPI A2A Protocol Wrapper**: Creates `app/fast_api_app.py`, exposing standard endpoints (`/run_sse`, `/a2a/app/`, and `/.well-known/agent-card.json`).

---

### Step 2: Implement Core Agent Logic & Function Tools

**Goal**: Define the `root_agent` persona and custom tools in `app/agent.py`.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Let's build the core logic for our personal-assistant agent in app/agent.py using the google-agents-cli-adk-code skill. 
> 1. Define two Python function tools: 'get_weather(query: str)' and 'get_current_time(query: str)' that return simulated responses.
> 2. Create the 'root_agent' using ADK Agent with model 'gemini-3.6-flash'.
> 3. Give root_agent system instructions outlining a warm, personable tone, explicit tool usage guidelines (only call weather/time when explicitly asked), and instructions on how to use user memories.
> ```

#### 🔍 Behind the Scenes (What `agy` and `agents-cli` are doing):
1. **Schema Reflection**: ADK inspects Python function type hints (`query: str`) and docstrings to automatically generate OpenAPI/Gemini function declarations (`FunctionDeclaration`).
2. **Agent Initialization**: `Agent(model="gemini-3.6-flash", tools=[...], instruction=...)` instantiates the root ADK agent.
3. **Prompt Guardrails**: System instructions define strict operational guidelines so Gemini knows when to trigger function calls vs when to respond directly.

---

### Step 3: Implement Context-Cached Memory Preloading

**Goal**: Integrate long-term memory retrieval without sacrificing Gemini Context Caching performance.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Implement a custom ADK tool named CachedPreloadMemoryTool in app/app_utils/memory_tool.py.
> It should override process_llm_request to search the user's Vertex AI Memory Bank for past facts, then append <PAST_CONVERSATIONS> memory context into the user's turn content.
> Make sure it skips processing on tool execution turns (turns containing function_response or function_call) so it never corrupts function response content items.
> ```

#### 🔍 Behind the Scenes (What `agy` and `agents-cli` are doing):
1. **The Context Caching Challenge**: Mutating `system_instruction` with user memories breaks Gemini's prompt cache hash, causing higher latency and token costs on every turn.
2. **The Memory Preloader Solution**: `CachedPreloadMemoryTool` hooks into `process_llm_request`. Before sending the request to Gemini, it queries Vertex AI Memory Bank for vector embeddings matching the user's input, then appends the retrieved facts directly into `llm_request.contents[-1]` (the user's message).
3. **100% Cache Preservation**: Because system instructions remain static, Gemini reuses the cached prompt prefix across all turns!
4. **Tool Turn Safety**: By checking for `function_response` items, the tool avoids injecting text into tool-execution turns, preventing `400 INVALID_ARGUMENT` API errors.

---

### Step 4: Test Interactively in the Local Agent Playground

**Goal**: Run a local web server to chat with your agent in a real-time browser UI.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Launch the local interactive agent playground using agents-cli playground so I can test my personal-assistant agent in my browser.
> ```

#### 🔍 Behind the Scenes (What `agy` and `agents-cli` are doing):
1. **Dev Server Launch**: `agents-cli playground` boots a local Uvicorn server hosting an interactive web client at `http://127.0.0.1:8080`.
2. **In-Memory State Simulation**: Uses `InMemorySessionService` and `InMemoryMemoryService` locally, allowing you to test multi-turn conversations and memory search without writing to Google Cloud databases.
3. **Event Streaming**: Streams Server-Sent Events (SSE) in real-time to render model thinking, text tokens, and tool calls as they execute.

---

### Step 5: Add Unit Tests & Run Code Formatting Checks

**Goal**: Enforce code quality and verify custom memory logic with automated tests.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> 1. Create a unit test in tests/unit/test_memory_tool.py using pytest-asyncio to verify that CachedPreloadMemoryTool attaches memory to user turns but leaves function_response turns completely untouched.
> 2. Format all python code using 'uv run black .' and verify formatting with 'uv run black --check .'.
> 3. Run unit tests with 'uv run pytest tests/unit'.
> ```

#### 🔍 Behind the Scenes (What `agy` and `agents-cli` are doing):
1. **Deterministic Formatter**: `black` parses Python code into Abstract Syntax Trees (ASTs) and formats whitespace according to PEP 8 standards.
2. **Isolated Unit Testing**: `pytest tests/unit` runs isolated tests with mock objects so CI/CD pipelines can run instantly without requiring GCP cloud credentials.
3. **Integration Test Separation**: Live LLM calls reside in `tests/integration/`, keeping fast feedback loops in `tests/unit/`.

---

### Step 6: Deploy to Vertex AI Agent Runtime & Publish

**Goal**: Host your agent on production Google Cloud infrastructure.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Use the google-agents-cli-deploy skill to deploy the personal-assistant agent to Vertex AI Agent Runtime in project '924128829435' and region 'us-central1'. Once deployed, show me the Agent Card URL.
> ```

#### 🔍 Behind the Scenes (What `agy` and `agents-cli` are doing):
1. **Container / Package Bundling**: `agents-cli deploy` packages `app/` and dependencies into a Cloud Storage artifact.
2. **Reasoning Engine Provisioning**: Calls Vertex AI API (`reasoningEngines.create`) to instantiate a managed runtime container running your ADK `Runner`.
3. **Agent Card Generation**: Serves an A2A-compliant `/.well-known/agent-card.json` listing skills, capabilities, and API schemas so other AI agents can discover and communicate with your personal assistant!

---

## ⚡ Useful `agy` Slash Commands to Try

When vibe coding with Antigravity, try these slash commands in your chat:

- **/goal**: Ask `agy` to run autonomous long-running tasks (e.g. *"Refactor memory service and verify tests until 100% passing"*).
- **/grill-me**: Interview mode where `agy` asks you clarifying design questions before building complex features.
- **/learn**: Persists custom coding preferences or setup fixes for future sessions.
- **/browser**: Allows `agy` to inspect web pages and documentation directly.

---

## 🎉 Congratulations!

You've built, tested, optimized, and deployed a production-grade AI Agent with **Google Antigravity (`agy`)** and **`agents-cli`**!
