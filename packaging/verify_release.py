"""End-to-end verification of the assembled Windows portable release."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

app_dir = Path(sys.argv[1]).resolve()
exe = app_dir / "AlgoPilot.exe"
runtime_test = Path(__file__).resolve().with_name("verify_portable_runtime.py")
port = 8765
base_url = f"http://127.0.0.1:{port}"
if not exe.is_file():
    raise SystemExit(f"missing executable: {exe}")

# Deliberately remove developer runtimes and compiler variables. This models a
# Windows computer with no Python, Node.js, MSYS2, MinGW or GDB on PATH.
keep_env = ("SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC", "PATHEXT")
env = {key: os.environ[key] for key in keep_env if key in os.environ}
system_root = env.get("SystemRoot", r"C:\Windows")
env["PATH"] = str(Path(system_root) / "System32")
env["ALGOPILOT_PORT"] = str(port)
stdout_path = app_dir.parent / "portable-test.stdout.log"
stderr_path = app_dir.parent / "portable-test.stderr.log"
with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
    process = subprocess.Popen([str(exe)], cwd=app_dir, env=env, stdout=stdout, stderr=stderr)
    try:
        health = None
        for _ in range(120):
            if process.poll() is not None:
                raise RuntimeError(f"packaged server exited with code {process.returncode}")
            try:
                with urllib.request.urlopen(f"{base_url}/api/health", timeout=3) as response:
                    health = json.load(response)
                break
            except Exception:
                time.sleep(1)
        if health is None:
            raise RuntimeError("packaged server did not become healthy")
        if health.get("status") != "ok" or not health.get("cpp_compiler") or not health.get("trace_cpp"):
            raise RuntimeError(f"health capability check failed: {health}")
        for route in ("/", "/learn/array"):
            with urllib.request.urlopen(base_url + route, timeout=10) as response:
                body = response.read()
                if response.status != 200 or b'<div id="app"' not in body:
                    raise RuntimeError(f"frontend/SPA check failed for {route}")
        print("HTTP_HEALTH=" + json.dumps(health, ensure_ascii=False))
        print("HTTP_INDEX_AND_SPA=200")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

result = subprocess.run([str(exe), "--exec-script", str(runtime_test)], cwd=app_dir, env=env)
if result.returncode:
    raise SystemExit(f"frozen runtime verification failed with code {result.returncode}")
