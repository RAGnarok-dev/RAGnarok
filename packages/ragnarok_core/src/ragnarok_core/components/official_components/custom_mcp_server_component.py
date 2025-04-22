import os
import subprocess
import tempfile
import shutil
import signal
from typing import Any, Dict, Tuple, Optional

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentOutputTypeOption,
    ComponentIOType,
    RagnarokComponent,
)

class CustomMCPServerComponent(RagnarokComponent):
    """
    Launch and manage a user-defined MCP server dynamically.

    Inputs:
      - server_name: Unique identifier for the MCP server (tool name).
      - server_code: Python code string defining the MCP server, must include FastAPI app or uvicorn invocation.
      - port: Port number on which the server will listen (default: 3333).
      - use_async: Whether to start the server asynchronously in the current process (True) or as a separate subprocess (False).

    Outputs:
      - base_url: URL where the MCP server is accessible (http://127.0.0.1:port).
      - pid: Process ID of the server if started as subprocess, or None if started asynchronously.
      - temp_dir: Path to the temporary directory containing server code.

    Methods:
      - stop(): Gracefully shuts down the subprocess and cleans up temporary files.
    """
    DESCRIPTION: str = "custom_mcp_server"
    ENABLE_HINT_CHECK: bool = False  # Allow arbitrary code without validation hints

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
                required=True,
            ),
            ComponentInputTypeOption(
                name="port",
                allowed_types={ComponentIOType.INT},
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
        server_code: str,
        port: int = 3333,
        use_async: bool = False
    ) -> Dict[str, Any]:
        # Validate code contains necessary FastAPI or uvicorn patterns
        if not ("FastAPI(" in server_code or "uvicorn.run" in server_code):
            raise ValueError(
                "Provided server_code must define a FastAPI app and uvicorn invocation."
            )

        # Create a temporary directory for server code
        temp_dir = tempfile.mkdtemp(prefix=f"mcp_{server_name}_")
        file_path = os.path.join(temp_dir, "server.py")

        # Write the server code to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(server_code)

        # Prepare environment and start command
        env = os.environ.copy()
        env["PORT"] = str(port)
        pid = None

        if use_async:
            # Start server programmatically using uvicorn
            import uvicorn  # type: ignore
            from threading import Thread

            def run_async():
                config = uvicorn.Config(
                    "server:app", host="0.0.0.0", port=port, log_level="info"
                )
                server = uvicorn.Server(config)
                server.run()

            thread = Thread(target=run_async, daemon=True)
            thread.start()
        else:
            # Launch server as subprocess
            process = subprocess.Popen(
                ["python", file_path],
                env=env,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            pid = process.pid

        base_url = f"http://127.0.0.1:{port}"
        return {"base_url": base_url, "pid": pid, "temp_dir": temp_dir}

    @classmethod
    def stop(cls, pid: Optional[int], temp_dir: str) -> None:
        """
        Stop the MCP server subprocess and remove temporary files.
        """
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        # Clean up temporary directory
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
