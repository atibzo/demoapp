
import os, time, uuid
def rid(): return f"req_{uuid.uuid4().hex[:6]}"
def now_ms(): return int(time.time()*1000)
def env(name, default=None):
    v = os.getenv(name, default)
    if v is None: raise RuntimeError(f"Missing env: {name}")
    return v
