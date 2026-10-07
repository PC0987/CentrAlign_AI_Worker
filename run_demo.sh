#!/usr/bin/env bash
set -e
if [ ! -d .venv ]; then python3 -m venv .venv; fi
. .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --host 127.0.0.1 --port 8000
