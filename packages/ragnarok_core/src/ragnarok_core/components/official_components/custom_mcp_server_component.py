import os
import sys
import subprocess
import tempfile
import shutil
import signal
import time
from typing import Optional, Dict, Any, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)


class CustomMCPServerComponent(RagnarokComponent):
    """
    Launch and manage a custom MCP server instance with isolated environment.

    Inputs:
      - server_name: Unique identifier for the instance.
      - server_code: Python code defining a FastAPI/Uvicorn app.
      - port: (Optional) TCP port to listen on (default 3333).
      - dependencies: (Optional) Space-separated PyPI packages to install.

    Outputs:
      - base_url: URL where the server is reachable.
      - pid: Process ID if launched as subprocess, else None.
      - temp_dir: Path to the temporary workspace.
    """
    DESCRIPTION = "custom_mcp_server"
    ENABLE_HINT_CHECK = False

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(name="server_name", allowed_types={ComponentIOType.STRING}, required=True),
            ComponentInputTypeOption(name="server_code", allowed_types={ComponentIOType.STRING}, required=True),
            ComponentInputTypeOption(name="port", allowed_types={ComponentIOType.INT}, required=False),
            ComponentInputTypeOption(name="dependencies", allowed_types={ComponentIOType.STRING}, required=False),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(name="base_url", type=ComponentIOType.STRING),
            ComponentOutputTypeOption(name="pid", type=ComponentIOType.INT),
            ComponentOutputTypeOption(name="temp_dir", type=ComponentIOType.STRING),
            ComponentOutputTypeOption(name="cmd",        type=ComponentIOType.LIST_STRING),
        )

    @classmethod
    def execute(
        cls,
        server_name: str,
        server_code: str,
        port: int = 3333,
        dependencies: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Prepare temporary workspace
        temp_dir = tempfile.mkdtemp(prefix=f"mcp_{server_name}_")
        env = os.environ.copy()
        port = port or 3333
        env["PORT"] = str(port)

        # Create virtual environment
        venv_dir = os.path.join(temp_dir, "venv")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir], env=env)
        bin_dir = os.path.join(venv_dir, "Scripts" if os.name == "nt" else "bin")
        python_exec = os.path.join(bin_dir, "python")
        pip_exec = os.path.join(bin_dir, "pip")
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

        # Install dependencies if provided
        if dependencies:
            deps = dependencies.split()
            subprocess.check_call(
                [pip_exec, "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", *deps],
                cwd=temp_dir,
                env=env
            )

        # Write server code
        script_path = os.path.join(temp_dir, "server.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(server_code)
        cmd = [python_exec, script_path]
        # Launch server as subprocess
        proc = subprocess.Popen(
            cmd,
            cwd=temp_dir,
            env=env,
            # stdout=subprocess.STDOUT,
            # stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        pid = proc.pid

        # Allow startup, then check for immediate errors
        time.sleep(2)
        if proc.poll() is not None:
            out, err = proc.communicate()
            raise RuntimeError(f"Server failed to start. stdout:\n{out}\nstderr:\n{err}")
        # base_url暂时不用
        base_url = f"http://127.0.0.1:{port}"
        
        return {
            "base_url": base_url,
            "pid":      pid,
            "temp_dir": temp_dir,
            "cmd":      cmd,
        }

    @classmethod
    def stop(cls, pid: Optional[int], temp_dir: str) -> None:
        # Terminate process if needed
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        # Cleanup workspace
        shutil.rmtree(temp_dir, ignore_errors=True)
