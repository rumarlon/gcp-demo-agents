# 🛠️ Workshop Deployment Guide: Multi-User Setup for Gemini Enterprise & Vertex AI

This guide provides step-by-step instructions for running hands-on workshops with multiple participants deploying AI agents into a shared Google Cloud Platform (GCP) project, **Vertex AI Agent Runtime**, and **Gemini Enterprise App Platform (GEAP)** / **Agent Gateway**.

---

## 🎯 Objective & Unique Naming Strategy

When multiple participants deploy agents in the same GCP project, default agent names like `personal-assistant` will collide in:
1. **Vertex AI Agent Runtime (Reasoning Engine)** display names.
2. **Gemini Enterprise (GEAP) / Agent Gateway** registered service endpoints.
3. **Google Cloud Logging** filtering and telemetry streams.

To avoid collisions, each participant is assigned a **Unique Participant Suffix** (e.g., `-alice`, `-user01`, `-jsmith`).

---

## 📋 Step-by-Step Participant Setup

### Step 1: Choose Your Unique Suffix
Pick a unique suffix that identifies your deployment:
- **Example Suffix**: `-alice`
- **Your Agent Name**: `personal-assistant-alice`

---

### Step 2: Update Agent Display Name in Project Files

Before deploying, update the agent display name in the following **3 key files** inside `agents/personal-assistant/`:

#### 1. Deployment Manifest (`agents-cli-manifest.yaml`)
- **File**: `agents-cli-manifest.yaml`
- **Change**: Update the `name` field.
```yaml
# BEFORE
name: "personal-assistant"

# AFTER (Replace -alice with your suffix)
name: "personal-assistant-alice"
```
> **Note**: `agents-cli` uses this manifest name when creating the Vertex AI Reasoning Engine resource and GEAP registration.

#### 2. Project Metadata (`pyproject.toml`)
- **File**: `pyproject.toml`
- **Change**: Update the package `name`.
```toml
# BEFORE
[project]
name = "personal-assistant"

# AFTER
[project]
name = "personal-assistant-alice"
```

#### 3. FastAPI Server Title (`app/fast_api_app.py`)
- **File**: `app/fast_api_app.py`
- **Change**: Update `app.title` around line 77.
```python
# BEFORE
app.title = "personal-assistant"

# AFTER
app.title = "personal-assistant-alice"
```

---

### Step 3: Test Locally Before Cloud Deployment

Verify that your customized agent builds and runs locally without errors:

```bash
cd agents/personal-assistant

# Install dependencies
uv sync --dev

# Run unit and integration tests
uv run pytest

# Launch local interactive playground
uv run agents-cli playground
```

Access the playground at `http://127.0.0.1:8080` to interact with your agent locally.

---

### Step 4: Deploy to Vertex AI Agent Runtime

Run `agents-cli deploy` to package and deploy your unique agent instance to Google Cloud:

```bash
agents-cli deploy
```

`agents-cli` will read your updated `agents-cli-manifest.yaml`, provision a dedicated Reasoning Engine endpoint with your display name (`personal-assistant-alice`), and output your unique **Agent Card URL**:

```text
✅ Deployment Complete!
Agent Runtime ID: projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>
Agent Card URL: https://us-central1-aiplatform.googleapis.com/reasoningEngines/v1/projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<REASONING_ENGINE_ID>/api/a2a/app/.well-known/agent-card.json
```

---

### Step 5: Register with Gemini Enterprise (GEAP) & Agent Gateway

To register your deployed agent into Gemini Enterprise without colliding with other participants:

```bash
# Register unique agent with Gemini Enterprise
agents-cli publish gemini-enterprise \
  --project="<YOUR_PROJECT_ID>" \
  --location="us-central1"
```

Because your agent has a unique display name (`personal-assistant-alice`), GEAP will register it as a distinct tool/agent in the Enterprise catalog.

---

### Step 6: Isolate Telemetry & Cloud Logs

To view your agent's structured **Intent vs. Outcome logs** in Google Cloud Logging:

1. Open **Google Cloud Console** > **Logging** > **Logs Explorer**.
2. Filter logs specifically for your agent:
```text
jsonPayload.agent_name="personal-assistant-alice"
```
3. Observe your agent's intent, tool calls (`get_weather`, `get_current_time`), and outcome latency metrics isolated from other workshop attendees.

---

## 🧹 Post-Workshop Cleanup

When the workshop concludes, clean up your individual cloud resources:

```bash
# Delete your specific Reasoning Engine deployment
gcloud ai reasoning-engines delete <REASONING_ENGINE_ID> --location="us-central1"
```
