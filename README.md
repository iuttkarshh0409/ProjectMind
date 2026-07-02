# ProjectMind 🧠

> A localized Change Impact & Review Obligation Engine that maps system dependencies and predicts downstream human review duties before code shifts turn into silent bugs.

ProjectMind is **not** an AI documentation generator, code refactoring assistant, or static linter. Its single mission is to answer one critical question:
**"I changed X. What else in the project should a human review before assuming the system remains coherent?"**

---

## ⚡ The ProjectMind Thesis

Every meaningful code modification creates **downstream obligations** elsewhere in the system. While developers are great at identifying direct import chains, they frequently miss implicit or cross-system assumptions (e.g., changing a configuration port that breaks a docker-compose map, updating a validation schema that breaks a database seeder, or altering database parameters that drift away from setup documentation).

ProjectMind maps these architectural assertions **deterministically** first, compiles a highly relevant context graph, and leverages LLM-structured reasoning to generate actionable human review checklists.

---

## 📐 System Architecture

ProjectMind runs entirely as a local CLI pipeline divided into six decoupled layers:

```
[Git Diff + Workspace] ──> [Deterministic Heuristics] ──> [Structured Graph Context]
                                                                 │
[Actionable Review Cards] <── [Schema Validator] <── [Gemini API (Structured JSON)]
```

1.  **Layer 1: Repository Scanner:** Deterministically captures active Git diffs and folder files, ignoring caches (`__pycache__`, `.pytest_cache`, `coverage`) and execution reports.
2.  **Layer 2: Knowledge Extraction:** Employs regex extractors to identify configurations, database settings, class declarations, API routing decorators, and environment variables.
3.  **Layer 3: Project Knowledge Model:** Maps file metadata and configurations into a semantic layout.
4.  **Layer 4: Change Analyzer:** Maps Git diff modifications directly to affected entities.
5.  **Layer 5: Impact Analysis (Deterministic Candidate Finder):** Traverses the knowledge graph to select candidate review files. Matches are categorized and ranked into `HIGH`, `MEDIUM`, and `LOW` confidence bands based on relationship strength (e.g., config maps, shared DB ports, test suites).
6.  **Layer 6: LLM Review Engine:** Prompts the Gemini API using structured JSON schema configurations to output validated, explanation-rich human review obligations citing explicit file evidence.

---

## 🛠️ Installation & Setup

ProjectMind relies on **`uv`** for fast Python packaging and dependency synchronization.

### 1. Prerequisites
Ensure you have `uv` installed:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Configure Gemini API Key
Provide your Gemini API token by setting the `GEMINI_API_KEY` environment variable:
```powershell
$env:GEMINI_API_KEY="your-gemini-api-key"
```

---

## 🚀 Usage

Navigate to any Git repository (or the included demo project) and run:

```powershell
uv run projectmind review
```

### Output Format
The console will display color-coded review obligation cards:

```
==================================================
REVIEW OBLIGATIONS
==================================================

[HIGH] Docker Compose port mapping mismatch
Confidence: HIGH
Area: Infrastructure Config
Reason:
  The application's default PORT has changed from 8080 to 9000. The docker-compose.yml file explicitly maps port 8080. This needs review to ensure the application is accessible and correctly configured within the Docker environment. Verify if the docker-compose.yml should expose port 9000 instead of 8080, or if the application should be configured to run on 8080 when deployed via Docker Compose.
Evidence:
  - docker-compose.yml
```

### Explainability Log
On every execution, ProjectMind generates a detailed execution report: [`.projectmind-report.md`](file:///d:/ai-agents/examples/demo-project/.projectmind-report.md) in the current running directory. This report documents:
*   The raw Git diff analyzed.
*   The full deterministic workspace snapshot table.
*   Selected candidate files and their scores.
*   The exact prompt text submitted.
*   The raw JSON payload returned by the LLM.
*   Sanitized final review cards.

---

## 🧪 Evaluation Repositories

ProjectMind has been validated end-to-end across multiple codebases:

*   **`examples/demo-project`:** Purpose-built configuration and port tracking demo.
*   **`aeris-v2`:** A Python FastAPI telemetry drift analyzer. Testing involved introducing a new Pydantic schema field (`environment`), which ProjectMind successfully linked to SQLite table structures and repository persistence APIs.
*   **`habit-cadence`:** A Turso/libsql habit tracker. Shifting DB connection strings flagged corresponding seed scripts and data migrations.
*   **`OrgSync`:** A Node.js/Express task manager. Changing backend configuration ports correctly flagged Docker compose services, Nginx configurations, and Vite React frontend api controllers.
*   **`alumconnect-alumassist`:** A Groq-integrated career mentor. Modifying FastAPI uvicorn settings flagged corresponding application documents.

---

## ⚙️ Development & Testing

Run the test suite using pytest via `uv`:
```powershell
uv run --with pytest pytest tests/
```

### Project Structure
*   [`projectmind/models.py`](file:///d:/ai-agents/projectmind/models.py): Internal representations and structured response schemas.
*   [`projectmind/workspace.py`](file:///d:/ai-agents/projectmind/workspace.py): Git command and directory metadata preprocessing.
*   [`projectmind/candidate_finder.py`](file:///d:/ai-agents/projectmind/candidate_finder.py): Proximity and configuration key match scores.
*   [`projectmind/llm_provider.py`](file:///d:/ai-agents/projectmind/llm_provider.py): Gemini structured API interface.
*   [`projectmind/validator.py`](file:///d:/ai-agents/projectmind/validator.py): Schema sanitization and file presence rules.
*   [`projectmind/reporter.py`](file:///d:/ai-agents/projectmind/reporter.py): Console formatting.
