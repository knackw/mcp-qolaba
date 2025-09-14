# Troubleshooting

This document collects common issues and how to fix them when working on the Qolaba API MCP Server.

## JetBrains AI Assistant: 400 error – "LLMChatAssistantMessageTool must have a tool name that is specified in the tools list in the parameters"

### Symptom
- In the IDE chat you see a 400 error similar to:
  - `LLM returned error response: ... code 400: LLMChatAssistantMessageTool must have a tool name that is specified in the tools list in the parameters`

### Root cause
- The chat session contains a tool call from the assistant, but the request sent by the IDE does not include a matching tool definition in its `tools` list. This can happen when:
  - A chat is continued across IDE restarts or model/provider changes and the tool list was not re‑initialized.
  - The selected model/provider in the IDE does not support tools.
  - A custom gateway/proxy filters the `tools` parameter.

This repository’s workflows expect tool support (e.g., for project search, file edits, and status updates). When the IDE does not expose these tools to the model, the assistant’s tool call fails with the error above.

### Fix
1. Start a fresh chat/session in the IDE (do not reuse a stale conversation).
2. Update to the latest JetBrains IDE + AI Assistant plugin.
3. In Settings → Tools → AI Assistant:
   - Choose a model/profile that supports tools (not a “text‑only” mode).
   - If there is a toggle for “Allow tool usage”, enable it.
4. If you use a custom provider/gateway, ensure the `tools` array is forwarded and contains the tools expected by this project. Typical tools used here are:
   - `functions.update_status`
   - `functions.submit`
   - `functions.search_project`
   - `functions.get_file_structure`
   - `functions.open`
   - `functions.open_entire_file`
   - `functions.scroll_down`
   - `functions.scroll_up`
   - `functions.create`
   - `functions.search_replace`
   - `functions.undo_edit`
   - `functions.ask_user`
   - `functions.bash`
5. If the error persists, completely close the IDE, delete the chat conversation, and start a new one.

### Why this matters here
- Our development workflow requires the assistant to call tools (e.g., to edit files and update status). If tools are not available to the model, it will fail with the error above. Ensuring the IDE provides the `tools` list resolves the problem.

---

## Running tests locally (Windows)
If running tests fails with "pytest is not installed":

```powershell
# From the repository root in PowerShell
python -m pip install -U pip
python -m pip install -e .[dev]
python -m pytest -q
```

If you prefer `uv`, you can run:

```powershell
uv pip install -e .[dev]
uv run pytest -q
```

Ensure you have a Python 3.10+ interpreter selected in your IDE/terminal.

---

## Environment variables
- Copy `.env.example` to `.env` and set the required values. The settings loader supports both `.env` and real environment variables at runtime.

```text
QOLABA_API_KEY=your_key
QOLABA_API_BASE_URL=https://api.qolaba.ai
QOLABA_ENV=development
```

If you run into missing-credential errors in `production`/`staging`, switch `QOLABA_ENV=development` for local development or set the required credentials.
