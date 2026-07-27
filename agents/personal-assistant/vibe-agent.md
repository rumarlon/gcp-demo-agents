# 🎨 Vibe Coding Experience: Replicate `personal-assistant` with `agy` & `agents-cli`

Welcome! This guide is designed for developers who are **new to Google Antigravity (`agy`) and Google Agents CLI (`agents-cli`)**. 

"Vibe Coding" means describing what you want in natural language while your AI pair programmer (**Antigravity**) uses specialized **Agent Development Kit (ADK) skills** to execute the heavy lifting—scaffolding projects, writing clean code, running local tests, and deploying to Google Cloud Platform (GCP).

---

## 🧭 Key Concepts for Beginners

Before starting, here is a quick primer on the tools powering this experience:

| Tool / Skill | What It Is | How It Helps You |
| :--- | :--- | :--- |
| **`agy` (Antigravity)** | Google's autonomous AI coding assistant. | Operates in your terminal/IDE to edit code, execute commands, run tests, and manage subagents. |
| **`agents-cli`** | Google's Agent Development Kit CLI tool. | Handles project scaffolding (`scaffold`), interactive browser testing (`playground`), evaluations (`eval`), and cloud deployment (`deploy`). |
| **ADK Agent Skills** | Specialized skills loaded inside `agy`. | Teaches `agy` production patterns for ADK Python APIs, Memory Bank integration, and Vertex AI deployments. |

---

## 🛠️ Step 0: Prerequisites & Initial Environment

1. **Install `uv` (Fast Python Package Manager)**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Install `google-agents-cli`**:
   ```bash
   uv tool install google-agents-cli
   ```
3. **Authenticate Google Cloud SDK**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

---

## 🚀 Step-by-Step Vibe Coding Workflow

Follow these 6 logical steps. For each step, **copy and paste the provided `agy` prompt** into your Antigravity chat window!

---

### Step 1: Scaffold the ADK Agent Project

**What this step does**: Generates a standard, production-ready ADK project layout using `agents-cli scaffold create`.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Create a new Google ADK agent project named 'personal-assistant' in the directory 'agents/personal-assistant' using the google-agents-cli-scaffold skill. Configure it for Python 3.12 with uv and set the deployment target to 'agent_runtime'. Include a FastAPI server wrapper and basic project structure.
> ```

**What `agy` will do**:
- Executes `agents-cli scaffold create agents/personal-assistant --deployment-target agent_runtime`.
- Creates `pyproject.toml`, `app/agent.py`, `app/fast_api_app.py`, and `deployment_metadata.json`.

---

### Step 2: Implement Core Agent Logic & Simulated Tools

**What this step does**: Builds the `root_agent` persona and declares function tools (`get_weather` and `get_current_time`) in `app/agent.py`.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Let's build the core logic for our personal-assistant agent in app/agent.py using the google-agents-cli-adk-code skill. 
> 1. Define two Python function tools: 'get_weather(query: str)' and 'get_current_time(query: str)' that return simulated responses.
> 2. Create the 'root_agent' using ADK Agent with model 'gemini-3.6-flash'.
> 3. Give root_agent system instructions outlining a warm, personable tone, explicit tool usage guidelines (only call weather/time when explicitly asked), and instructions on how to use user memories.
> ```

**What `agy` will do**:
- Creates clean type-annotated tool functions with docstrings.
- Configures `root_agent` with Gemini 3.6 Flash and strict `TOOL USAGE GUIDELINES` to prevent unnecessary tool calls.

---

### Step 3: Implement Context-Cached Memory Preloading

**What this step does**: Integrates Vertex AI Memory Bank. Creates a custom tool `CachedPreloadMemoryTool` that attaches long-term memory facts directly into user turn content.

> 💡 **Why this matters**: Injected memories attached to user turn content guarantee a **100% Gemini Context Cache hit rate**, preventing system instruction mutation latency spikes!

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Implement a custom ADK tool named CachedPreloadMemoryTool in app/app_utils/memory_tool.py.
> It should override process_llm_request to search the user's Vertex AI Memory Bank for past facts, then append <PAST_CONVERSATIONS> memory context into the user's turn content.
> Make sure it skips processing on tool execution turns (turns containing function_response or function_call) so it never corrupts function response content items.
> ```

**What `agy` will do**:
- Implements `CachedPreloadMemoryTool` inheriting from ADK's `BaseTool`.
- Safely inspects `llm_request.contents[-1].parts` to avoid modifying function response turns.

---

### Step 4: Test Interactively in the Local Agent Playground

**What this step does**: Launches a local web browser UI to chat with your agent, test weather/time tool calls, and inspect session state.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Launch the local interactive agent playground using agents-cli playground so I can test my personal-assistant agent in my browser.
> ```

**What `agy` will do**:
- Executes `uv run agents-cli playground`.
- Opens `http://127.0.0.1:8080` in your browser for real-time interactive pair testing.

---

### Step 5: Add Unit Tests & Run Code Formatting Checks

**What this step does**: Verifies the memory preloader with unit tests and validates code formatting with Black.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> 1. Create a unit test in tests/unit/test_memory_tool.py using pytest-asyncio to verify that CachedPreloadMemoryTool attaches memory to user turns but leaves function_response turns completely untouched.
> 2. Format all python code using 'uv run black .' and verify formatting with 'uv run black --check .'.
> 3. Run unit tests with 'uv run pytest tests/unit'.
> ```

**What `agy` will do**:
- Writes unit tests with mocks for `search_memory`.
- Formats code with `black`.
- Verifies that all unit tests pass (100%).

---

### Step 6: Deploy to Vertex AI Agent Runtime & Publish

**What this step does**: Hosts your agent in Google Cloud Vertex AI Reasoning Engine and publishes it for enterprise use.

> 💬 **Copy & Paste this `agy` prompt into Antigravity:**
> ```text
> Use the google-agents-cli-deploy skill to deploy the personal-assistant agent to Vertex AI Agent Runtime in project '924128829435' and region 'us-central1'. Once deployed, show me the Agent Card URL.
> ```

**What `agy` will do**:
- Runs `agents-cli deploy --project 924128829435 --region us-central1 --no-confirm-project`.
- Outputs your live Reasoning Engine endpoint and Agent Card JSON (`/.well-known/agent-card.json`).

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
