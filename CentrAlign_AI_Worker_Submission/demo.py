import json
import sys
from app.agent import run_task

TASK = sys.argv[1] if len(sys.argv) > 1 else "Find the latest invoice from Acme Corporation, extract the amount and due date, enter it into our internal system, and tell me once it is done."
result = run_task(TASK)
print(json.dumps(result, indent=2))
