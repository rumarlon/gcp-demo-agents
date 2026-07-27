# Google Cloud AI Agents Repository (`gcp-agents`)

> [!IMPORTANT]
> **Disclaimer & Usage Notice**: This repository and its sample code are provided "as-is" for educational and demonstration purposes, without warranty or liability of any kind. Executing, testing, or deploying these agents may incur Google Cloud Platform (GCP) charges (such as Vertex AI API calls, Reasoning Engine deployments, or Memory Bank usage). Please monitor your GCP billing dashboard and resource usage accordingly.

Welcome to the **gcp-agents** repository! This repository hosts a collection of production-ready AI agents built with the [Google Agent Development Kit (ADK)](https://github.com/google/adk) and deployed on **Google Cloud Platform (GCP)** via **Vertex AI Agent Engine (Reasoning Engine)**, **Agent Gateway**, and **Gemini Enterprise**.

Each agent in this repository is designed as an isolated, modular subproject with its own dependencies, tests, deployment configuration, and documentation.

---

## 🤖 Available Agents Catalog

| Agent Name | Folder Path | Description | Key GCP Services |
| :--- | :--- | :--- | :--- |
| **Personal Assistant** | [`agents/personal-assistant/`](agents/personal-assistant/README.md) | Warm, responsive AI assistant with persistent long-term memory, real-time tools (time, weather), and Agent-to-Agent (A2A) support. | Vertex AI Agent Engine, Memory Bank, Model Armor, Gemini Enterprise |

---

## 📂 Repository Layout

```text
gcp-agents/
├── README.md                      # Top-level repository overview & guidelines
├── .gitignore                     # Global git ignore policy
├── LICENSE                        # Apache 2.0 Open Source License
├── .github/
│   └── workflows/
│       └── ci.yml                 # Automated testing CI workflow for all agents
└── agents/                        # Container folder for all AI agents
    └── personal-assistant/        # Personal Assistant Agent
        ├── app/                   # Agent source code (ADK agent & FastAPI server)
        │   ├── agent.py           # ADK App & Root Agent definition
        │   ├── fast_api_app.py    # FastAPI server & A2A protocol router
        │   └── app_utils/         # Helpers, Memory Bank tools, & plugins
        │       └── model_armor_plugin.py # Google Cloud Model Armor security plugin
        ├── tests/                 # Integration and unit test suite
        ├── deployment_metadata.json # Deployment target metadata for agents-cli
        ├── agents-cli-manifest.yaml # agents-cli project manifest
        ├── pyproject.toml         # Python project dependencies (managed by uv)
        ├── Dockerfile             # Container definition
        ├── GEMINI.md              # Agent system prompt & personality guidance
        ├── vibe-agent.md          # Step-by-step vibe coding guide with agy prompts
        └── README.md              # Detailed Agent documentation & architecture diagram
```

---

## 🛠️ Prerequisites & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/rumarlon/gcp-agents.git
   cd gcp-agents
   ```

2. **Python 3.12+** and **`uv` package manager**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Google Cloud SDK (`gcloud`)**:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Google Antigravity (`agy`)** (Optional but recommended):
   - **Desktop App**: Download and launch the Google Antigravity desktop app from [antigravity.google/download](https://antigravity.google/download).
   - **Antigravity CLI (`agy`)**: Install and run `agy` directly in your terminal:
     ```bash
     uv tool install agy
     # Launch agy in your terminal:
     agy
     ```

5. **Google Agents CLI (`agents-cli`)**:
   ```bash
   uv tool install google-agents-cli
   ```

### ⚡ Quick Start: Local Agent Playground (No Cloud Infrastructure Required)
You can immediately clone this repository and test agents locally without creating GCP cloud resources, Agent Gateways, or Gemini Enterprise apps:

```bash
git clone https://github.com/rumarlon/gcp-agents.git
cd gcp-agents/agents/personal-assistant
uv sync --dev
uv run agents-cli playground
```
This launches the local interactive agent playground in your browser at `http://127.0.0.1:8080`.

### ☁️ Cloud Deployment & Agent Gateway Setup
When you are ready to deploy to GCP:
- **Vertex AI Agent Engine (Reasoning Engine)** hosting: Enable `aiplatform.googleapis.com` and run `agents-cli deploy`.
- **Optional Enterprise Integration (Agent Gateway & Gemini Enterprise)**:
  1. Enable `agentgateway.googleapis.com` in GCP.
  2. Create an Agent Gateway via `curl` REST API or `gcloud`: `https://agentgateway.googleapis.com/v1/projects/<PROJECT_ID>/locations/us-central1/gateways?gatewayId=<GATEWAY_NAME>`.
  3. Find your Gemini Enterprise App ID in the Search & Conversation console.
  4. Run `agents-cli publish gemini-enterprise`.

For detailed, step-by-step creation commands, see [`agents/personal-assistant/README.md`](agents/personal-assistant/README.md#step-1-create-an-agent-gateway-using-gcloud--rest-api).

---

## ➕ Adding a New Agent

To add a new agent to this repository:

1. Create a new directory under `agents/<agent-name>/`:
   ```bash
   mkdir -p agents/my-new-agent
   ```
2. Initialize an ADK project structure:
   ```bash
   agents-cli scaffold create agents/my-new-agent --deployment-target agent_runtime
   ```
3. Add tests in `agents/<agent-name>/tests/`.
4. Include a dedicated `README.md` detailing requirements, services used, and workflow diagrams.
5. Submit a pull request. The CI workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) will automatically test your agent.

---

## 📄 License

Distributed under the Apache 2.0 License. See `LICENSE` for more information.
