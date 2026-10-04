# PolicyProof MCP Server

A minimal, production-ready Model Context Protocol (MCP) server for the PolicyProof insurance agent ecosystem. Built using the official Python MCP SDK with remote HTTP/SSE transport, designed to be registered as an MCP connector in AgenticOrg.

> **Note**: This server provides deterministic evidence retrieval tools only. It does not contain an AI agent, call LLMs, or make coverage decisions/recommendations. All decision logic resides in the autonomous agent (AgenticOrg).

---

## 🛠️ Tools Exposed

### 1. `health_check`
- **Description**: Verifies that the PolicyProof MCP server is online and operational.
- **Inputs**: None
- **Response**:
  ```json
  {
    "status": "ok",
    "service": "PolicyProof MCP"
  }
  ```

### 2. `search_policy_evidence`
- **Description**: Retrieves factual policy evidence records, page numbers, excerpts, and document URLs matching a given `policy_id` and query string.
- **Inputs**:
  - `policy_id` (`string`): Identifier of the insurance policy (e.g. `POL-AUTO-2024`, `POL-HOME-889`).
  - `query` (`string`): Search terms or topic keywords (e.g. `windshield`, `water damage`).
- **Response**:
  ```json
  {
    "policy_id": "POL-AUTO-2024",
    "query": "windshield",
    "results": [
      {
        "source": "[TEST DATA] Auto Policy Section 4 - Comprehensive & Collision",
        "page": 12,
        "excerpt": "[TEST DATA] Glass Breakage: Comprehensive coverage includes windshield repair and replacement with a $0 deductible when utilizing preferred network repair facilities.",
        "source_url": "https://example.com/test-data/policies/POL-AUTO-2024.pdf#page=12"
      }
    ]
  }
  ```

---

## 🌐 Endpoints

- **MCP SSE Transport Endpoint**: `http://localhost:8000/sse` (or `http://127.0.0.1:8000/sse`)
- **MCP Message Post Endpoint**: `http://localhost:8000/messages`
- **HTTP Monitoring Health Endpoint**: `http://localhost:8000/health` (returns JSON status for cloud deployment health monitors)

---

## 🚀 Windows Local Run Instructions

### 1. Prerequisites
- Python 3.10+ installed and added to `PATH`.

### 2. Create and Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Start the MCP Server
```powershell
python server.py
```
Or directly via `uvicorn`:
```powershell
uvicorn server:app --host 0.0.0.0 --port 8000
```

---

## ☁️ Cloud Deployment (Render / Railway)

The server dynamically reads the listening port from the `PORT` environment variable provided by cloud hosts:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server.py` (or `uvicorn server:app --host 0.0.0.0 --port $PORT`)
- **Health Check Path**: `/health`

---

## 🔌 AgenticOrg Connector Configuration

When adding this tool server in AgenticOrg:
- **Transport Type**: `SSE` / `Remote MCP`
- **Server URL**: `http://127.0.0.1:8000/sse` (Local) or `https://<your-deployed-app>.render.com/sse` (Cloud)
