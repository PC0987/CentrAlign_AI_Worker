# CentrAlign Autonomous AI Worker — Invoice Operator

A narrow, working proof-of-concept for the CentrAlign AI Engineering assignment.

## What it does

The worker accepts a natural-language task such as:

> Find the latest invoice from Acme Corporation, extract the amount and due date, enter it into our internal system, and tell me once it is done.

It then:

1. Understands the intended outcome and identifies the vendor.
2. Generates an explicit execution plan.
3. Uses a real browser (Playwright + Chromium) to operate a simulated company environment.
4. Observes the invoice list and opens the latest matching invoice.
5. Extracts the amount and due date from the rendered invoice page.
6. Applies a safety policy: invoices above the approval threshold pause for human approval.
7. Enters the data into the simulated accounts-payable system.
8. Re-opens the created ERP record and independently verifies the result.
9. Returns evidence links and an execution trace.

This intentionally focuses on one business workflow instead of pretending to automate every company task.

## Architecture

```text
User task
   |
   v
Intent / task understanding
   |
   v
Planner --> ordered action plan
   |
   v
Agent runtime
   |---- Browser tool (Playwright)
   |---- Policy / human approval gate
   |---- Observation + state
   |---- Retry / fallback locator
   |
   v
Verification
   |
   v
Evidence + concise completion summary
```

## Project structure

- `app/main.py` — FastAPI server + simulated company applications + API endpoints.
- `app/planner.py` — task understanding and plan creation.
- `app/agent.py` — autonomous execution loop, browser control, approval gate, recovery, verification.
- `app/store.py` — in-memory sandbox data.
- `static/index.html` — simple operator UI showing the execution trace and outcome.
- `demo.py` — CLI demo runner.
- `tests/` — unit tests for planning behavior.

## Run locally

### 1. Create an environment

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install a Playwright browser

The included worker uses Chromium through Playwright. In a normal local environment:

```bash
playwright install chromium
```

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

### 5. Run the CLI demo

```bash
python demo.py
```

## Demo scenarios

### A. Fully autonomous happy path

```text
Find the latest invoice from Acme Corporation, extract the amount and due date, enter it into our internal system, and tell me once it is done.
```

Expected behavior: selects `INV-ACME-1002`, creates an AP record, and verifies it.

### B. Human-in-the-loop safety gate

```text
Find the latest invoice from Zenith Systems, extract the amount and due date, enter it into our internal system, and tell me once it is done.
```

The simulated Zenith invoice is above the default ₹10,000 approval threshold, so the agent stops before the consequential ERP write and asks for approval. Clicking **Approve & continue** resumes execution.

## Design decisions

### Why a simulated company environment?

The assignment explicitly allows a sandbox/mock environment and prohibits real credentials or unauthorized third-party access. Keeping the environment local makes the prototype deterministic and safe while still exercising actual browser interactions.

### Why Playwright?

The objective is execution, not just explanation. Playwright gives the worker an actual browser tool with rendered UI, clicks, form entry, and observation.

### Why verify by re-reading the ERP record?

The worker does not assume that a successful click means success. It independently re-opens the created record and compares vendor, invoice ID, amount, and due date.

### Why a local planner?

The prototype runs without an external model/API key, making the submitted repository reproducible. The planner is isolated so a production version can replace `planner.py` with an LLM-backed structured planner while keeping the tool runtime and verification architecture intact.

## Failure handling

- If the primary invoice link locator fails, the agent uses a DOM fallback locator.
- If no invoice matches the vendor, the task fails explicitly with a useful error.
- High-value invoices pause for approval before changing the internal system.
- Verification failure is treated as a failed task, not as success.

## Optional LLM mode

The default mode is fully local and reproducible. To let the intent-understanding layer use an OpenAI-compatible model, set `MODEL_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally `OPENAI_MODEL`. The worker falls back to the local planner if the external call fails.

## Known limitations

- The environment currently supports invoice-processing tasks only.
- Company data is in memory and resets with the process.
- The local planner is deterministic rather than a general-purpose LLM planner.
- Browser automation targets a controlled sandbox rather than arbitrary third-party websites.
- Authentication, distributed task queues, persistent memory, and production observability are not implemented in this prototype.

## What I would build next

1. Replace the deterministic planner with structured LLM planning plus schema validation.
2. Add a persistent memory layer for company policies and historical outcomes.
3. Introduce a reusable tool registry for browser, files, APIs, email, and desktop applications.
4. Add durable task queues, retries, idempotency, and audit logs.
5. Build an evaluation harness with task suites, success metrics, recovery metrics, and regression tests.
6. Add permissions and fine-grained approval policies per action/tool/risk level.

## Models / frameworks / services

- Python 3.11+
- FastAPI
- Playwright
- Chromium
- Pydantic
- No real company credentials or private data
- No external paid API is required to run the submitted prototype

## Assignment alignment

The implementation demonstrates:

- Understanding the user's intended outcome
- Determining required actions
- Planning
- Tool selection
- Real browser execution
- Observation
- Adaptation / fallback
- State and context
- Human approval
- Independent verification
- Evidence and completion summary

The core loop is implemented as:

**Goal → Understand → Plan → Execute → Observe → Adapt → Verify → Complete**

## Submission checklist

- [x] GitHub-ready source code
- [x] README with setup/run instructions
- [x] Architecture explanation
- [x] Technical/design decisions
- [ ] Demo video or hosted live demo — record locally using the included demo flow
- [x] Known limitations
- [x] Next steps
- [x] Assumptions
- [x] Models/APIs/frameworks disclosure

## Suggested 90-second demo narration

"I built a narrow autonomous invoice worker rather than a simulated chat agent. I give it one natural-language outcome. It interprets the goal, generates a plan, opens a real browser against a sandbox company inbox, finds the latest invoice, extracts the required fields, checks policy, enters the payable into the internal ERP, then re-opens the record and verifies the result. For a high-value invoice it pauses before the write and asks a human for approval. The important design choice is that completion is based on verified state and evidence, not on the model simply saying the task is done."
