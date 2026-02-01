import json
import time
import uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class Trace:
    trace_id: str

def new_trace() -> Trace:
    return Trace(trace_id=str(uuid.uuid4()))

def log_event(trace: Trace, event: str, **data) -> None:
    payload = {"ts": time.time(), "trace_id": trace.trace_id, "event": event, **data}
    print(json.dumps(payload, ensure_ascii=False))
