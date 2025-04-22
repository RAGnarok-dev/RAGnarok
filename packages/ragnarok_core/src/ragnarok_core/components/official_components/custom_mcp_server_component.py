import os
import subprocess
import tempfile
from typing import Any, Dict, Tuple

from ragnarok_toolkit.component import (
    ComponentInputTypeOption,
    ComponentIOType,
    ComponentOutputTypeOption,
    RagnarokComponent,
)

class CustomMCPServerComponent(RagnarokComponent):
    """
    Dynamically start a user-defined MCP server from provided Python code.

    Inputs:
      - server_code: Python code string defining an MCP server (e.g., FastAPI app).
      - port: Port number to run the server on (default 3333).

    Outputs:
      - base_url: The base URL where the MCP server is accessible.
      - pid: Process ID of the spawned server process.
    """
    DESCRIPTION: str = "custom_mcp_server"
    ENABLE_HINT_CHECK: bool = False  # Skip hint validation for arbitrary code

    @classmethod
    def input_options(cls) -> Tuple[ComponentInputTypeOption, ...]:
        return (
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
        )

    @classmethod
    def output_options(cls) -> Tuple[ComponentOutputTypeOption, ...]:
        return (
            ComponentOutputTypeOption(name="base_url", type=ComponentIOType.STRING),
            ComponentOutputTypeOption(name="pid", type=ComponentIOType.INT),
        )

    @classmethod
    def execute(cls, server_code: str, port: int = 3333) -> Dict[str, Any]:
        # Create a temporary file to hold the server code
        tmp_dir = tempfile.mkdtemp(prefix="mcp_server_")
        file_path = os.path.join(tmp_dir, "server.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(server_code)

        # Launch the server in a separate process
        # Assuming user code handles --port argument or reads PORT env var
        env = os.environ.copy()
        env["PORT"] = str(port)
        process = subprocess.Popen(
            ["python", file_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=tmp_dir,
        )

        base_url = f"http://127.0.0.1:{port}"
        # Return the URL and PID
        return {"base_url": base_url, "pid": process.pid}
