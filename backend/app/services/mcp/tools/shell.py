"""AIEco - Shell MCP Tools (Sandboxed)"""
import asyncio
import subprocess
from typing import Any, Dict


async def execute(action: str, params: Dict[str, Any]) -> Any:
    """Execute shell commands (sandboxed)"""
    if action == "execute":
        return await run_command(
            params["command"],
            params.get("cwd"),
            params.get("timeout", 30)
        )
    raise ValueError(f"Unknown shell action: {action}")


async def run_command(command: str, cwd: str = None, timeout: int = 30) -> Dict[str, Any]:
    """Run a shell command with timeout"""
    # Safety checks - block dangerous commands
    dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
    if any(d in command.lower() for d in dangerous):
        return {"success": False, "error": "Command blocked for safety"}
    
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        
        return {
            "success": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace")
        }
    except asyncio.TimeoutError:
        proc.kill()
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e)}
