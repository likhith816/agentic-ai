# SteelMind AI Wizard

> **Multimodal Multi-Agent AI Maintenance Decision Support System for Steel Plant Operations**  
> *Tata Steel AI Hackathon 2026 — Round 2 (Agentic AI Challenge)*  
> **Developer:** Likhith Sai Parepalli  
> **Tagline:** *"See it. Say it. Solve it."*

---

## 📋 Overview

Steel manufacturing plants operate complex, capital-intensive, and interdependent equipment. Unplanned downtime can cost thousands of dollars per minute, raise safety risks, and create massive operational bottlenecks. 

In practice, maintenance engineers must cross-reference fragmented information sources—such as paper manuals, Standard Operating Procedures (SOPs), historical breakdown logs, and live sensor telemetry—to determine the right repair action.

**SteelMind AI Wizard** is an enterprise-grade, context-aware decision-support platform that consolidates these diverse data sources. It accepts **Voice + Image + Text + CSV + PDF** inputs to deliver:
* Faster, explainable fault diagnosis (RAG + Vision).
* Proactive anomaly detection and Remaining Useful Life (RUL) prediction.
* Risk-based prioritization of maintenance actions based on procurement and delay constraints.
* Automated digital log entries and structured PDF reports.
* A feedback loop that updates the local vector store with engineering corrections.

---

## ⚙️ Core Features

1. **Multi-Agent Orchestration (LangGraph)**: Uses a Directed Acyclic Graph (DAG) state machine where 8 specialized agents collaborate to analyze, diagnose, score risk, and generate recommendations.
2. **Predictive Maintenance Dashboard**: Visualizes live plant KPIs, Remaining Useful Life (RUL) predictions from an XGBoost regressor, and statistical sensor anomaly flags from an Isolation Forest model.
3. **Multimodal Inputs**:
   * **Voice Transcription**: Local speech-to-text transcription via OpenAI Whisper, with voice synthesis response feedback.
   * **Visual Damage Inspector**: Feeds damage photographs to Gemini 1.5 Flash to automatically detect fractures, leaks, corrosion, or wear.
4. **Knowledge Retrieval (RAG)**: Integrates and reasons over loaded equipment manuals and SOP PDFs using a local FAISS vector store with SentenceTransformers embeddings.
5. **Convex Online Cloud Database**: Syncs session diagnostics history and engineer feedback logs to the Convex cloud platform. Features a smart local-memory/SQLite fallback, ensuring the application remains **100% functional offline** during evaluations.
6. **Onboarding Guide Chatbot**: A dedicated floating chat assistant in the bottom-right corner powered by Groq Llama 3.3. It guides new users on how to operate the platform and walk through plant equipment troubleshooting.
7. **Engineering Reports**: Generates downloadable, structured technical report PDFs containing action lists and spare parts summaries.
8. **Feedback-Driven Learning**: When engineers confirm or correct a diagnosis, the feedback updates the local FAISS index so the system learns from historical outcomes.

---

## 🧠 System Workflow & Architecture

SteelMind routes inputs and executes nodes in a parallelized, structured pipeline managed by LangGraph:

```
                  ┌────────────────────────┐
                  │      Orchestrator      │ (Determines input types & routes)
                  └───────────┬────────────┘
                              │
             ┌────────────────┼────────────────┐ (Parallel Agent Execution)
             ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Vision Agent │ │  RAG Agent   │ │Anomaly Agent │
     │ (Gemini 1.5) │ │ (FAISS/Mini) │ │  (IsoForest) │
     └───────┬──────┘ └───────┬──────┘ └───────┬──────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                  ┌────────────────────────┐
                  │    Diagnostic Agent    │  ◄── (Llama 3.3 via Groq)
                  └───────────┬────────────┘
                              ▼
                  ┌────────────────────────┐
                  │      Risk Scorer       │ (Calculates LOW/MED/HIGH/CRITICAL)
                  └───────────┬────────────┘
                              ▼
                  ┌────────────────────────┐
                  │    Report Generator    │  ──► (Compiles PDF + Markdown)
                  └───────────┬────────────┘
                              ▼
                  ┌────────────────────────┐
                  │     Feedback Agent     │  ──► (FAISS updates & Convex Sync)
                  └────────────────────────┘
```

### Workflow Logic:
1. **Orchestrator Node**: Validates the inputs (image path, sensor CSV path, custom doc paths, or voice recording).
2. **Parallel Fan-out**:
   * **Vision Node** analyzes damage images for structural defects.
   * **RAG Node** queries the local FAISS database for matching SOP steps.
   * **Anomaly Node** scales sensor fields, flags statistical outliers via Isolation Forest, and regresses RUL via XGBoost.
3. **Synthesis & Diagnosis**:
   * **Diagnostic Node** merges the visual, textual, and mathematical telemetry outputs into a coherent root-cause diagnosis.
   * **Risk Scorer Node** scores the operational severity, overriding to `CRITICAL` if the RUL is less than 7 days.
   * **Report Node** compiles the printable PDF report.
   * **Feedback Node** logs the outcome, syncs to Convex, and appends engineering overrides to the vector database.

---

## 📁 Repository Structure

```
steelmind-ai-wizard/
├── convex/                       ← Convex database schemas, queries, and mutations
├── src/                          ← Core backend source files
│   ├── agents/                   ← Specialized agent nodes (vision, RAG, ML, etc.)
│   ├── graph/                    ← LangGraph pipeline and routing DAG
│   ├── models/                   ← Pre-trained ML models (.pkl files)
│   ├── knowledge_base/           ← FAISS database index files & raw SOP documents
│   ├── data/                     ← Data generation scripts and CSV tables
│   └── utils/                    ← Voice, vision, and database utility modules
├── frontend/                     ← React, Vite, and Tailwind CSS UI dashboard
├── tests/                        ← pytest suite for backend API endpoints
├── main.py                       ← FastAPI server entry point
├── run_demo.ps1                  ← Automated local startup script
├── requirements.txt              ← Python packages listing
└── .env                          ← Local environment variables configuration
```

---

## 🚀 Installation & Setup

### Prerequisites
* **Python 3.11+**
* **Node.js v18+**

### 1. Setup API Keys & Environment Config
Copy `.env.example` to `.env` and configure the following variables:
```bash
# Groq API Keys (Llama reasoning model)
GROQ_API_KEY=your_groq_api_key

# Google AI Studio API Keys (Gemini vision model)
GOOGLE_API_KEY=your_google_api_key

# Convex Database Settings (Online Cloud Sync)
CONVEX_DEPLOYMENT=your_convex_deployment_name
CONVEX_URL=https://your-project.convex.cloud
CONVEX_SITE_URL=https://your-project.convex.site
```

### 2. Automated Run (PowerShell)
You can start the entire application including data generation, model training, and launching both backend and frontend servers with one command:
```powershell
./run_demo.ps1
```

### 3. Manual Step-by-Step Run

#### A. Install Backend Dependencies & Train Models
```bash
# Install packages
pip install -r requirements.txt

# Seed synthetic IoT sensor telemetry and maintenance records
python src/data/generate_sensor_data.py
python src/data/generate_maintenance_logs.py
python src/data/generate_knowledge_docs.py

# Train ML models (Isolation Forest, StandardScaler, and XGBoost RUL)
python src/models/train_models.py

# Build the FAISS Vector database index
python src/knowledge_base/index_docs.py
```

#### B. Setup Convex Cloud Database
Ensure Convex is initialized to host the schemas and functions online:
```bash
# Install npm dependencies at root
npm install

# Start Convex dev deployment (will prompt to sign up/login and push functions)
npx convex dev
```

#### C. Start backend server
```bash
python main.py
```
*The FastAPI backend will start running on [http://localhost:8000](http://localhost:8000).*

#### D. Start Frontend Dashboard
Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
*The React Vite panel will start running on [http://localhost:5173](http://localhost:5173).*

---

## 🧪 Testing

The backend includes a comprehensive test suite covering the API routes, telemetry metrics, and guide fallbacks. To execute the tests:

```bash
pytest -v
```

All 6 core test cases will execute and verify the health of the system:
* `test_health_check`: Verifies FastAPI server and agent dependencies are operational.
* `test_list_equipment`: Checks equipment metadata matches valid schema ids.
* `test_predictions`: Verifies ML prediction engine accurately queries RUL lists.
* `test_service_overdue`: Validates database overhaul schedules.
* `test_plant_summary`: Checks dashboard aggregate KPI card endpoints.
* `test_guide_assistant_fallback`: Ensures guide chatbot operates and recovers cleanly.

---

## 📄 License
This project is licensed under the MIT License.
