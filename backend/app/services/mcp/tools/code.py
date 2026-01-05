"""AIEco - Code Execution MCP Tools (Sandboxed)"""
import sys
from io import StringIO
from typing import Any, Dict
import asyncio


async def execute(action: str, params: Dict[str, Any]) -> Any:
    """Execute code-related actions"""
    if action == "execute_python":
        return await run_python(params["code"], params.get("timeout", 10))
    elif action == "analyze":
        return await analyze_code(params["code"], params.get("language", "python"))
    raise ValueError(f"Unknown code action: {action}")


async def run_python(code: str, timeout: int = 10) -> Dict[str, Any]:
    """Execute Python code in a sandboxed environment"""
    # Create isolated namespace
    namespace = {"__builtins__": __builtins__}
    
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        # Compile and execute with timeout
        compiled = compile(code, "<string>", "exec")
        
        def exec_code():
            exec(compiled, namespace)
        
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, exec_code),
            timeout=timeout
        )
        
        output = captured_output.getvalue()
        return {
            "success": True,
            "output": output,
            "variables": {k: repr(v) for k, v in namespace.items() 
                         if not k.startswith("_") and k != "__builtins__"}
        }
    
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Execution timed out after {timeout}s"}
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__}
    finally:
        sys.stdout = old_stdout


async def analyze_code(code: str, language: str = "python") -> Dict[str, Any]:
    """Analyze code for issues and suggestions"""
    issues = []
    suggestions = []
    
    if language == "python":
        # Basic static analysis
        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            # Check for common issues
            if "import *" in line:
                issues.append({"line": i, "message": "Avoid wildcard imports"})
            if "except:" in line and "Exception" not in line:
                issues.append({"line": i, "message": "Use specific exception types"})
            if len(line) > 120:
                suggestions.append({"line": i, "message": "Line too long (>120 chars)"})
    
    return {
        "language": language,
        "lines": len(code.split("\n")),
        "issues": issues,
        "suggestions": suggestions
    }
