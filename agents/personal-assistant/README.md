# Personal Assistant Agent (`personal-assistant`)

> [!IMPORTANT]
> **Disclaimer & Usage Notice**: This repository and its sample code are provided "as-is" for educational and demonstration purposes, without warranty or liability of any kind. Executing, testing, or deploying these agents may incur Google Cloud Platform (GCP) charges (such as Vertex AI API calls, Reasoning Engine deployments, or Memory Bank usage). Please monitor your GCP billing dashboard and resource usage accordingly.

A production-ready personalized AI assistant built with the **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Platform (GCP)**. It features persistent long-term memory extraction via **Vertex AI Memory Bank**, real-time simulated tools (weather, time), and Agent-to-Agent (A2A) protocol support for enterprise integration.

---

## 🌟 Key Features & Capabilities

- **Warm & Personable Conversational Persona**: Maintains an engaging, helpful tone, acknowledges introductions, and addresses users by name.
- **Persistent Long-Term Memory**: Automatically extracts, stores, and preloads user facts and preferences across sessions using Vertex AI Memory Bank.
- **Real-time Tool Execution**: Includes function declarations for retrieving current weather and time information.
- **Agent-to-Agent (A2A) Protocol**: Built-in FastAPI endpoints supporting A2A inter-agent communication.
- **Enterprise Ready**: Fully deployed to Vertex AI Agent Runtime and integrated with Gemini Enterprise App & Agent Gateway.

---

## 🔄 Agent Workflow Architecture

The following diagram illustrates how user requests flow through the Gemini Enterprise / Agent Gateway layer, the FastAPI server, the ADK Root Agent, and underlying GCP Vertex AI services.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Gemini Enterprise
    participant GW as Agent Gateway / A2A Protocol
    participant App as FastAPI Server (fast_api_app.py)
    participant Runner as ADK Runner & Root Agent (app/agent.py)
    participant MemoryBank as Vertex AI Memory Bank Service
    participant Gemini as Gemini 3.6 Flash (Vertex AI)
    participant Tools as Agent Tools (Weather, Time)

    User->>GW: Send user prompt / message
    GW->>App: POST /a2a/app (A2A RPC request)
    App->>Runner: Execute session run with Runner
    
    rect rgb(240, 248, 255)
        note over Runner,MemoryBank: Step 1: Memory Preloading
        Runner->>MemoryBank: PreloadMemoryTool (Retrieve user facts/preferences)
        MemoryBank-->>Runner: Return <PAST_CONVERSATIONS> memory context
    end

    Runner->>Gemini: Generate content (Prompt + Memory Context + Tool Declarations)
    
    alt Model decides to call a tool
        Gemini-->>Runner: Return FunctionCall (e.g., get_weather / get_current_time)
        Runner->>Tools: Execute function (e.g., get_weather("San Francisco"))
        Tools-->>Runner: Return Tool Result ("60 degrees and foggy")
        Runner->>Gemini: Send FunctionResponse to Gemini
    end

    Gemini-->>Runner: Final model text response
    
    rect rgb(255, 245, 238)
        note over Runner,MemoryBank: Step 2: Long-Term Memory Extraction
        Runner->>MemoryBank: after_agent_callback (generate_memories_callback)
        MemoryBank-->>MemoryBank: Asynchronously extract facts & save to Memory Bank
    end

    Runner-->>App: Return final response turn
    App-->>GW: A2A JSON Response
    GW-->>User: Present response to user
```

---

## ☁️ Google Cloud Services Used

| Google Cloud Service | Component / File | Purpose & Role |
| :--- | :--- | :--- |
| **Vertex AI Agent Engine (Reasoning Engine)** | [`deployment_metadata.json`](deployment_metadata.json) | Managed cloud runtime that hosts and runs the agent container in `us-central1`. |
| **Google Cloud Model Armor** | [`app/app_utils/model_armor_plugin.py`](app/app_utils/model_armor_plugin.py) | Security screening service protecting prompts and LLM outputs against prompt injection, jailbreaks, PII leakage, CSAM, and malicious URLs. |
| **Vertex AI Memory Bank Service** | [`app/app_utils/services.py`](app/app_utils/services.py) | Stores extracted long-term memories (user preferences, facts) across deployments. |
| **Vertex AI Session Service** | [`app/app_utils/services.py`](app/app_utils/services.py) | Manages multi-turn conversation sessions persistently. |
| **Gemini 3.6 Flash (`gemini-3.6-flash`)** | [`app/agent.py`](app/agent.py) | Core Large Language Model for reasoning, text generation, and function calling. |
| **Gemini Enterprise & Agent Gateway** | User Defined | Exposes the agent to enterprise chat apps and gateways. |
| **Cloud Logging & OpenTelemetry** | [`app/fast_api_app.py`](app/fast_api_app.py) | Structured logging, error collection, and open-telemetry tracing in GCP Console. |

---

## 📋 Requirements & Prerequisites

### System Requirements
- **Python**: `3.12` or higher
- **Package Manager**: [`uv`](https://astral.sh/uv) (recommended)
- **Google Cloud SDK**: `gcloud` CLI installed and authenticated

### Google Cloud Permissions
Your GCP identity / Service Account requires the following IAM roles:
- `roles/aiplatform.user` (Vertex AI Agent Engine & Gemini model access)
- `roles/logging.logWriter` (Cloud Logging)
- `roles/storage.objectAdmin` (if storing artifacts in GCS)

---

## 🚀 Local Development & Running

### 1. Environment Configuration

Copy the example environment file and fill in your GCP project details:
```bash
cp .env.example .env
```

`.env` example content:
```env
GOOGLE_CLOUD_PROJECT=<YOUR_PROJECT_ID>
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
MODEL_NAME=gemini-3.6-flash
```

### 2. Install Dependencies
```bash
uv sync --dev
```

### 3. Run Local Agent Playground
Launch the interactive web-based Agent Playground locally using `uv run` (to ensure SSL certificates and virtualenv dependencies are loaded):
```bash
uv run agents-cli playground
```
This opens an interactive local chat interface in your browser at `http://127.0.0.1:8080` to interact with the agent, test tool calls, and inspect session state.



---

## 🧪 Testing & Evaluation

### Run Test Suite
Run unit, integration, and server E2E tests:
```bash
uv run pytest
```

### Run Evaluation Benchmarks
Run multi-turn quality and task success evaluations using `google-agents-cli`:
```bash
agents-cli eval run
```
View evaluation results generated in `artifacts/grade_results/`.

---

## 🚢 Deployment & Integration Guide

### 1. Local Testing (No Cloud Setup Required)
You do **not** need an Agent Gateway or GCP deployment to test and develop locally.
Simply run:
```bash
uv run agents-cli playground
```
This opens an interactive local chat interface at `http://127.0.0.1:8080`.

---

### 2. Deploy to Vertex AI Agent Engine (Reasoning Engine)
To host the agent on managed Google Cloud infrastructure:

1. **Enable Vertex AI API**:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=<YOUR_PROJECT_ID>
   ```
2. **Deploy the Agent**:
   ```bash
   agents-cli deploy --no-confirm-project
   ```
   Upon completion, `agents-cli` outputs your **Reasoning Engine Resource ID** (e.g. `projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<ENGINE_ID>`).

---

### 3. Optional: Agent Gateway & Gemini Enterprise Setup

If you want to integrate your deployed agent with **Gemini Enterprise** or **Agent Gateway**, follow these setup steps:

#### Prerequisites
- A Google Cloud Project with **Gemini Enterprise** (formerly Vertex AI Search and Conversation / Agent Builder) enabled.
- An existing Gemini Enterprise App/Engine. You can find your App ID in the [Vertex AI Search & Conversation Console](https://console.cloud.google.com/gen-app-builder/engines).

#### Step 1: Create an Agent Gateway (Using `gcloud` / REST API)
1. **Enable the Agent Gateway API**:
   ```bash
   gcloud services enable agentgateway.googleapis.com --project=<YOUR_PROJECT_ID>
   ```

2. **Create an Agent Gateway Instance via `curl` REST API**:
   ```bash
   curl -X POST \
     -H "Authorization: Bearer $(gcloud auth print-access-token)" \
     -H "Content-Type: application/json" \
     "https://agentgateway.googleapis.com/v1/projects/<YOUR_PROJECT_ID>/locations/us-central1/gateways?gatewayId=<YOUR_GATEWAY_NAME>" \
     -d '{
       "displayName": "My Agent Gateway",
       "description": "Agent Gateway for inter-agent A2A routing"
     }'
   ```

3. **Obtain Gateway Resource Path**:
   Your created Agent Gateway resource path follows this format:
   `projects/<YOUR_PROJECT_NUMBER>/locations/us-central1/gateways/<YOUR_GATEWAY_NAME>`

#### Step 2: Publish Agent to Gemini Enterprise
Register your deployed Reasoning Engine with your Gemini Enterprise App and Agent Gateway:
```bash
agents-cli publish gemini-enterprise \
  --app-id "projects/<YOUR_PROJECT_NUMBER>/locations/us/collections/default_collection/engines/<YOUR_APP_ID>" \
  --agent-gateway "projects/<YOUR_PROJECT_NUMBER>/locations/<LOCATION>/gateways/<YOUR_AGENT_GATEWAY_NAME>"
```

> [!NOTE]
> Replace `<YOUR_PROJECT_NUMBER>`, `<YOUR_LOCATION>`, `<YOUR_APP_ID>`, and `<YOUR_AGENT_GATEWAY_NAME>` with your specific GCP resource values. Do not commit actual project numbers or private gateway names to git.

---

## 🛡️ Security & Model Armor Integration

To protect your agent against **prompt injection, jailbreaks, PII/sensitive data leakage, CSAM, and malicious URLs**, Google Cloud Model Armor is configured at both the Gemini Enterprise App level and the ADK Agent Runtime level.

### 1. Gemini Enterprise App Model Armor Configuration

Model Armor templates define security policies (e.g. prompt injection detection, jailbreak filters, malicious URLs, CSAM, sensitive PII leakage).

#### How Model Armor Templates are Generated and Updated in GCP:

You can generate and upload Model Armor templates to GCP using **3 different methods**:

##### Method 1: Google Cloud CLI (`gcloud`)
1. **Enable Model Armor API**:
   ```bash
   gcloud services enable modelarmor.googleapis.com --project=<YOUR_PROJECT_ID>
   ```

2. **Generate & Upload Template**:
   ```bash
   gcloud model-armor templates create <YOUR_TEMPLATE_ID> \
     --project=<YOUR_PROJECT_ID> \
     --location=<YOUR_LOCATION> \
     --filter-config="pi_and_jailbreak_filter_settings={confidence_level=HIGH},malicious_uri_filter_settings={filter_enforcement=ENABLED},rai_settings={rai_filters=[{filter_type=HATE_SPEECH,confidence_level=MEDIUM_AND_ABOVE},{filter_type=HARASSMENT,confidence_level=MEDIUM_AND_ABOVE},{filter_type=DANGEROUS,confidence_level=MEDIUM_AND_ABOVE},{filter_type=SEXUALLY_EXPLICIT,confidence_level=MEDIUM_AND_ABOVE}]}"
   ```

##### Method 2: Programmatic REST API / `curl`
You can generate templates via REST API request to the Model Armor service:
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  -H "X-Goog-User-Project: <YOUR_PROJECT_ID>" \
  -H "Content-Type: application/json" \
  "https://modelarmor.<YOUR_LOCATION>.rep.googleapis.com/v1/projects/<YOUR_PROJECT_ID>/locations/<YOUR_LOCATION>/templates?templateId=<YOUR_TEMPLATE_ID>" \
  -d '{
    "filterConfig": {
      "piAndJailbreakFilterSettings": {
        "filterEnforcement": "ENABLED",
        "confidenceLevel": "HIGH"
      },
      "maliciousUriFilterSettings": {
        "filterEnforcement": "ENABLED"
      },
      "raiSettings": {
        "raiFilters": [
          { "filterType": "HATE_SPEECH", "confidenceLevel": "MEDIUM_AND_ABOVE" },
          { "filterType": "HARASSMENT", "confidenceLevel": "MEDIUM_AND_ABOVE" },
          { "filterType": "DANGEROUS", "confidenceLevel": "MEDIUM_AND_ABOVE" },
          { "filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "MEDIUM_AND_ABOVE" }
        ]
      }
    }
  }'
```

##### Method 3: Google Cloud Console UI
1. Navigate to **Gemini Enterprise > Security > Configuration**:
   `https://console.cloud.google.com/gemini-enterprise/locations/<YOUR_LOCATION>/engines/<YOUR_APP_ID>/security/configuration?project=<YOUR_PROJECT_ID>`
2. Click **Create Security Template** or **Configure Model Armor**.
3. Select desired security policies:
   - **Prompt Injection & Jailbreak**: High confidence
   - **Malicious URLs**: Enabled
   - **Responsible AI Safety Filters** (`MEDIUM_AND_ABOVE`): Hate Speech, Harassment, Dangerous Content, Sexually Explicit
4. Click **Save**. GCP generates the template resource automatically.

#### Attaching the Template to Gemini Enterprise:
Once the template is generated in GCP, copy its full resource path:
```text
projects/<YOUR_PROJECT_ID>/locations/<YOUR_LOCATION>/templates/<YOUR_TEMPLATE_ID>
```
In the [Gemini Enterprise Security Console](https://console.cloud.google.com/gemini-enterprise/locations/<YOUR_LOCATION>/engines/<YOUR_APP_ID>/security/configuration?project=<YOUR_PROJECT_ID>), select this template for both **User Prompt Template** and **Response Template** and click **Save**.

### 2. ADK Plugin Backend Protection (`ModelArmorPlugin`)

The ADK agent runtime incorporates [`ModelArmorPlugin`](app/app_utils/model_armor_plugin.py) via ADK `BasePlugin`:

- **Environment Variables**:
  ```env
  MODEL_ARMOR_PROJECT_ID=<YOUR_PROJECT_ID>
  MODEL_ARMOR_LOCATION=<YOUR_LOCATION>
  MODEL_ARMOR_TEMPLATE_ID=<YOUR_TEMPLATE_ID>
  MODEL_ARMOR_STRICT_MODE=false
  ```
- **Behavior**:
  - `before_model_callback`: Calls `SanitizeUserPrompt` to inspect incoming user prompts.
  - `after_model_callback`: Calls `SanitizeModelResponse` to inspect outgoing model outputs.
  - **Graceful Fallback**: If Model Armor is unconfigured in local offline testing, the plugin logs a debug notice and allows traffic to pass without interruption.
