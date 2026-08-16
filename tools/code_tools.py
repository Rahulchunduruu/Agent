"""Code execution tool: code_executor."""

import subprocess
import sys

from langchain_core.tools import tool


@tool
def code_executor(code: str, language: str = "python") -> str:
    """Executes code and returns the output. Supports python and bash."""
    try:
        if language == "python":
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True, timeout=15
            )
        elif language == "bash":
            result = subprocess.run(
                code, shell=True,
                capture_output=True, text=True, timeout=15
            )
        else:
            return f"Unsupported language: {language}"

        return result.stdout if result.stdout else result.stderr

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (15s limit)"
    except Exception as e:
        return f"Error: {str(e)}"
