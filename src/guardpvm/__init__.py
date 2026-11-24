# =============================================================================
# FILE PURPOSE:
# High-level Python SDK interface for GuardPVM.
# Provides Pythonic context managers (sandbox), child-process executors (run),
# and direct bindings to VM telemetry and step quotas.
# Usage: import guardpvm; res = guardpvm.run("while True: pass", step_quota=1000)
# =============================================================================

"""
GuardPVM Python SDK
High-level interface for step quotas, zero-division recovery, and runtime execution telemetry.
"""

import sys
import os
import subprocess
import json
from contextlib import contextmanager

__version__ = "1.0.0"

class GuardResult:
    def __init__(self, stdout, stderr, exit_code, stats=None):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.stats = stats or {}

    @property
    def ok(self):
        return self.exit_code == 0

    def __repr__(self):
        return f"<GuardResult exit_code={self.exit_code} steps={self.stats.get('steps_executed', 'N/A')}>"

def is_guard_runtime():
    """Checks if currently executing inside a GuardPVM custom runtime."""
    return hasattr(sys, "get_guard_stats") and hasattr(sys, "set_step_quota")

def get_stats():
    """Returns the current execution telemetry dict if running on GuardPVM."""
    if is_guard_runtime():
        return sys.get_guard_stats()
    return {"error": "Not running under GuardPVM interpreter"}

def reset_stats():
    """Resets execution stats to zero if running on GuardPVM."""
    if is_guard_runtime():
        sys.reset_guard_stats()

def set_step_quota(quota):
    """Sets the VM instruction step budget."""
    if is_guard_runtime():
        sys.set_step_quota(int(quota))
    else:
        raise RuntimeError("set_step_quota requires running under GuardPVM (guard-python).")

def set_div_mode(mode):
    """Sets zero division handling to 'strict' or 'recover'."""
    if is_guard_runtime():
        sys.set_div_mode(mode)
    else:
        raise RuntimeError("set_div_mode requires running under GuardPVM (guard-python).")

@contextmanager
def sandbox(step_quota=0, div_mode="strict"):
    """
    Context manager that temporarily applies quotas and div_mode.
    
    Example:
        with guardpvm.sandbox(step_quota=1000, div_mode="recover"):
            x = 10 / 0
    """
    if not is_guard_runtime():
        raise RuntimeError("guardpvm.sandbox() must be run with guard-python interpreter.")

    prev_quota = sys.get_step_quota()
    prev_mode = sys.get_div_mode()

    try:
        sys.set_div_mode(div_mode)
        if step_quota > 0:
            sys.set_step_quota(step_quota)
        yield
    finally:
        sys.set_div_mode(prev_mode)
        sys.set_step_quota(prev_quota)

def run(code, step_quota=0, div_mode="strict", executable="/usr/local/bin/guard-python"):
    """
    Executes Python code in an isolated GuardPVM subprocess and returns GuardResult with telemetry.
    Can be called from ANY Python interpreter (even stock CPython).
    """
    wrapper = f"""
import sys, json

try:
    if hasattr(sys, 'set_div_mode'):
        sys.set_div_mode({repr(div_mode)})
    if hasattr(sys, 'set_step_quota') and {step_quota} > 0:
        sys.set_step_quota({step_quota})
    
    exec({repr(code)})
except BaseException as e:
    sys.stderr.write(f'GuardPVM Exception: {{type(e).__name__}}: {{e}}\\n')
    sys.exit(1)
finally:
    if hasattr(sys, 'get_guard_stats'):
        stats = sys.get_guard_stats()
        print('__GUARDPVM_STATS_DELIMITER__')
        print(json.dumps(stats))
"""

    env = os.environ.copy()
    env.pop("GUARD_PVM_STEP_QUOTA", None)
    env["GUARD_PVM_DIV_MODE"] = div_mode

    proc = subprocess.run(
        [executable, "-c", wrapper],
        capture_output=True,
        text=True,
        env=env
    )

    stdout = proc.stdout
    stats = {}

    if "__GUARDPVM_STATS_DELIMITER__" in stdout:
        user_stdout, stats_json = stdout.split("__GUARDPVM_STATS_DELIMITER__", 1)
        stdout = user_stdout.strip()
        try:
            stats = json.loads(stats_json.strip())
        except Exception:
            pass

    return GuardResult(
        stdout=stdout,
        stderr=proc.stderr.strip(),
        exit_code=proc.returncode,
        stats=stats
    )
