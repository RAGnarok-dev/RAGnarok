import os
import sys
import subprocess
import tempfile
import shutil
import signal
from threading import Thread
import time
from typing import Any, Dict, Tuple, Optional

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)


class CustomMCPServerComponent1(RagnarokComponent):
    """
    A dynamic launcher for MCP servers, supporting both inline FastAPI/uvicorn code
    and external commands or packaged MCP servers.

    Inputs:
      - server_name: Unique identifier for the MCP server instance (used for temp dir prefix).
      - server_code: Optional Python code string defining a FastAPI app or uvicorn.run call.
      - port: TCP port where the server will listen (default: 3333).
      - dependencies: Optional space-delimited list of PyPI packages to install in the temp env.
      - command: Optional shell command to launch the server (bypasses server_code path).
      - use_async: If True, starts the server in a background thread (via uvicorn API).

    Outputs:
      - base_url: HTTP base URL of the running server (e.g. http://127.0.0.1:3333).
      - pid: Process ID if launched as subprocess, or None for async thread mode.
      - temp_dir: Path to temporary directory containing code and environment.
    """
    DESCRIPTION = "custom_mcp_server"
    ENABLE_HINT_CHECK = False  # Disable code validation hints for arbitrary server_code

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
            ComponentInputTypeOption(
                name="server_name",
                allowed_types={ComponentIOType.STRING},
                required=True,
            ),
            ComponentInputTypeOption(
                name="server_code",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
            ComponentInputTypeOption(
                name="port",
                allowed_types={ComponentIOType.INT},
                required=False,
            ),
            ComponentInputTypeOption(
                name="dependencies",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
            ComponentInputTypeOption(
                name="command",
                allowed_types={ComponentIOType.STRING},
                required=False,
            ),
            ComponentInputTypeOption(
                name="use_async",
                allowed_types={ComponentIOType.BOOL},
                required=False,
            ),
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(name="base_url", type=ComponentIOType.STRING),
            ComponentOutputTypeOption(name="pid", type=ComponentIOType.INT),
            ComponentOutputTypeOption(name="temp_dir", type=ComponentIOType.STRING),
        )

    @classmethod
    def execute(
        cls,
        server_name: str,
        server_code: Optional[str] = None,
        port: int = 3333,
        dependencies: Optional[str] = None,
        command: Optional[str] = None,
        use_async: bool = False,
    ) -> Dict[str, Any]:
        temp_dir = tempfile.mkdtemp(prefix=f"mcp_{server_name}_")
        env = os.environ.copy()
        env["PORT"] = str(port)

        venv_dir = os.path.join(temp_dir, "venv")
        subprocess.check_call([sys.executable, "-m", "venv", venv_dir], env=env)

        if os.name == "nt":
            python_exec = os.path.join(venv_dir, "Scripts", "python.exe")
            pip_exec = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            python_exec = os.path.join(venv_dir, "bin", "python")
            pip_exec = os.path.join(venv_dir, "bin", "pip")

        bin_dir = os.path.dirname(python_exec)
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

        if dependencies:
            deps = dependencies.split()
            print(f"[DEBUG] Installing dependencies: {deps}")
            subprocess.check_call(
                [pip_exec, "install", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", *deps],
                cwd=temp_dir,
                env=env
            )

        pid: Optional[int] = None

        if command:
            if "--port" not in command and "-p" not in command.split():
                command = f"{command} --port {port}"
            print(f"[DEBUG] Running command: {command}")
            process = subprocess.Popen(
                command.strip().split(),
                cwd=temp_dir,
                env=env,
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                stdout=sys.stdout,        # ← 直接打到终端
                stderr=sys.stderr,
                text=True,
            )
            pid = process.pid
        else:
            if not server_code:
                raise ValueError("server_code must be provided if no command is specified.")

            file_path = os.path.join(temp_dir, "server.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(server_code)

            print(f"[DEBUG] Written server code to: {file_path}")

            if use_async:
                def _run_uvicorn():
                    import uvicorn
                    config = uvicorn.Config("server:app", host="0.0.0.0", port=port, log_level="info")
                    server = uvicorn.Server(config)
                    server.run()

                thread = Thread(target=_run_uvicorn, daemon=True)
                thread.start()
                pid = None
            else:
                print(f"[DEBUG] Launching server via subprocess: {python_exec} {file_path}")
                process = subprocess.Popen(
                    [python_exec, file_path],
                    cwd=temp_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                pid = process.pid

                # 检查是否立即异常退出（常见错误：包未装、端口占用、语法错误）
                time.sleep(2)
                retcode = process.poll()
                if retcode is not None:
                    out, err = process.communicate()
                    print(f"[ERROR] MCP server exited early with code {retcode}")
                    print(f"[STDOUT]\n{out}")
                    print(f"[STDERR]\n{err}")
                    raise RuntimeError("MCP server failed to start. Check server_code or environment.")

        base_url = f"http://127.0.0.1:{port}"
        print(f"[INFO] MCP Server started at {base_url}, pid={pid}, temp_dir={temp_dir}")
        return {"base_url": base_url, "pid": pid, "temp_dir": temp_dir}

    @classmethod
    def stop(cls, pid: Optional[int], temp_dir: str) -> None:
        """
        Gracefully stop the MCP server (if subprocess) and clean up temp files.
        """
        # Terminate the subprocess if we have a PID
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass

        # Remove the temporary directory
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
