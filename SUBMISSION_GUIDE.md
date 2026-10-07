# CentrAlign submission guide

## What to submit

The assignment asks for a GitHub/source-code link, README, architecture/design explanation, demo video or live demo, limitations, next steps, assumptions, and a disclosure of models/APIs/frameworks used. The brief also says AI coding tools are allowed, but the candidate should be able to explain and modify the submitted implementation.

## Recommended repository name

`centralign-ai-worker`

## Recommended GitHub description

> Narrow autonomous enterprise AI worker that processes invoices end-to-end using browser automation, safety approvals, recovery, and independent verification in a local sandbox.

## GitHub upload

1. Create a new GitHub repository named `centralign-ai-worker`.
2. Upload the contents of this folder.
3. Confirm the repository root contains `README.md`, `requirements.txt`, `app/`, `static/`, `tests/`, and `demo.py`.
4. Run `python -m pytest -q` before sharing the URL.

## Demo video: 60–90 seconds

Use the normal task first:

> Find the latest invoice from Acme Corporation, extract the amount and due date, enter it into our internal system, and tell me once it is done.

Show these moments in the browser UI:

1. The task is entered.
2. The execution trace shows understand → plan → execute → observe.
3. The worker opens the invoice and extracts the fields.
4. The worker creates the AP record.
5. Verification completes and evidence is shown.

Then briefly show the safety path with:

> Find the latest invoice from Zenith Systems, extract the amount and due date, enter it into our internal system, and tell me once it is done.

Show that the worker stops for approval because the amount exceeds the threshold, then click **Approve & continue** and show the final verification.

### Suggested narration

> I built a narrow autonomous invoice worker instead of a chat-only demo. It takes a natural-language business outcome, understands the goal, creates an action plan, operates a real browser against a safe local company sandbox, observes the result, applies a human approval policy when the action is consequential, performs the ERP write, and independently verifies the final state. The key design choice is that success is based on verified state and evidence, not on the agent simply claiming completion.

## Form answers to paste

### Project title

CentrAlign Autonomous AI Worker — Invoice Operator

### One-line description

A narrow autonomous enterprise worker that turns a natural-language invoice request into verified browser-executed work with approval and recovery.

### Architecture

Natural-language task → structured intent → executable plan → browser tool → observe → policy/approval gate → ERP action → independent verification → evidence summary.

### Why this approach

The assignment explicitly values genuine autonomy over broad simulated functionality. This prototype focuses on one complete workflow and demonstrates planning, real execution, observation, recovery, approval, and verification in a safe sandbox.

### Models / APIs / frameworks

Python, FastAPI, Playwright, Chromium, Pydantic, HTTPX. The repository runs without an external model/API key using a deterministic local planner. An optional OpenAI-compatible planner can be enabled with `MODEL_PROVIDER=openai` and an API key. No real company credentials or private data are used.

### Limitations

The prototype supports invoice-processing tasks only; data is sandboxed and in memory; the local planner is not a general-purpose LLM; browser tools target the controlled environment; distributed queues, persistent enterprise memory, authentication, and production-grade observability are not implemented.

### Next steps

Add a validated LLM planner, persistent company memory, reusable tool/connector registry, durable queues and idempotency, richer permissions, and an evaluation harness for reliability and generalization.
