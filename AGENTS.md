# AGENTS.md - AI Agents & CodeX Operating Guidelines

> **IMPORTANT NOTICE FOR ALL AI AGENTS & CODEX RUNNERS**:
> You are operating in a private downstream fork of `AzurLaneAutoScript`. You MUST strictly follow the safety rules below. Failure to adhere to these rules may cause unwanted upstream disruption.

---

## 🚨 ABSOLUTE RED LINES (CRITICAL SAFETY RULES)

### 1. STRICTLY FORBIDDEN: Pull Requests (禁止创建任何 PR)
- **DO NOT create Pull Requests under ANY circumstances.**
- **DO NOT run `gh pr create`** or any script attempting to open a PR.
- **DO NOT call GitHub REST/GraphQL API** to create pull requests, issues, or reviews.
- This repository is a private fork owned by `ZerowindSE`. The upstream author (`LmeSzinc`) must NEVER be disturbed or sent merge requests.

### 2. STRICTLY FORBIDDEN: Pushing to Upstream (禁止向上游推送)
- **DO NOT run `git push upstream`** or push to `https://github.com/LmeSzinc/AzurLaneAutoScript.git`.
- All push commands MUST only target `origin` (`git@github.com:ZerowindSE/AzurLaneAutoScript.git`).
- Interacting with `upstream` is strictly limited to pulling updates:
  ```bash
  git fetch upstream
  git merge upstream/master
  ```

---

## 🛠️ Project Architecture & Conventions

### 1. Zero-Touch Upstream Codebase (纯增量开发原则)
- **DO NOT modify existing upstream files** (e.g., `alas.py`, `gui.py`, files in `module/campaign/`, `module/ocr/`, `module/webui/`, etc.).
- All custom additions, REST API endpoints, and Model Context Protocol (MCP) integrations must strictly reside inside:
  ```text
  module/api/
  ```

### 2. Standard Service Commands
- **Start REST API & MCP Server**:
  ```bash
  python run_api.py
  ```
- **Run MCP in stdio mode (for local agent host invocation)**:
  ```bash
  python run_api.py --mcp-stdio
  ```
- **Custom Port & Host**:
  ```bash
  python run_api.py --host 127.0.0.1 --port 8000
  ```

---

## 📋 Summary of Key Files
- `run_api.py`: Main launcher for REST API (FastAPI) and MCP (FastMCP / MCPServer).
- `module/api/service.py`: Core logic for game status tracking, OCR resource polling, and task scheduling.
- `module/api/router.py`: FastAPI routes for REST endpoints (`/api/status`, `/api/resources/refresh`, `/api/config/*`).
- `module/api/mcp_server.py`: MCP tool definitions (`get_alas_status`, `refresh_game_resources`, etc.).
- `API_README.md`: Full documentation for REST API and MCP usage.
- `SSH_SETUP.md`: Local SSH setup and remote synchronization instructions.
