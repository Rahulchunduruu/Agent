"""File management tools: file_system, write_file, read_file."""

import os
import subprocess

from langchain_core.tools import tool


@tool
def file_system(cmd: str) -> str:
    """
    Execute shell/terminal commands on the local machine. Works on Windows, Linux, and Mac.

    Common Commands (use correct OS syntax):

    LIST FILES:
    - Windows: 'dir'
    - Linux/Mac: 'ls -la'

    READ FILE:
    - Windows: 'type filename.txt'
    - Linux/Mac: 'cat filename.txt'

    DELETE FILE:
    - Windows: 'del filename.txt'
    - Linux/Mac: 'rm filename.txt'

    CREATE FOLDER:
    - Both: 'mkdir foldername'

    WRITE FILE (small content ONLY - under ~50 lines):
    - python -c "open('file.txt','w',encoding='utf-8').write('your content')"
    - For LARGE content (big files, 1000s of lines), NEVER use shell commands -
      use the write_file tool instead (bypasses the Windows 8191-char cmd limit).

    APPEND TO FILE (universal):
    - python -c "open('file.txt','a',encoding='utf-8').write('more content')"

    CHECK FILE EXISTS (universal):
    - python -c "import os; print(os.path.exists('file.txt'))"

    RUN PYTHON SCRIPT (universal):
    - 'python script.py'

    GET CURRENT DIRECTORY (universal):
    - python -c "import os; print(os.getcwd())"

    STRICT RULES:
    - NEVER use triple quotes (''' or \"\"\") in any command
    - NEVER use this for web searches — use web_search instead
    - NEVER use this for calculations — use calculator instead
    - NEVER pass large file content (more than ~50 lines) through this tool — use write_file instead
    - ALWAYS specify encoding='utf-8' when writing files via python -c
    - For multiline content, use \\n instead of actual newlines
    - Commands automatically time out after 60 seconds
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=60
        )
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        return result.stdout.strip() or "Command executed successfully."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def write_file(file_path: str, content: str, append: bool = False) -> str:
    """Write text content to a file (UTF-8). Safe for very large content (10,000+ lines)
    because it writes directly via Python I/O — no shell escaping or command-line length limits.
    Use this INSTEAD of file_system whenever you need to create or update file contents.
    - append=False (default): creates or OVERWRITES the file.
    - append=True: adds content to the end of the file. Use this to write huge files
      in multiple chunks when the content is too big for a single call.
    Parent folders are created automatically."""
    try:
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(content)

        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        size = os.path.getsize(file_path)
        action = "Appended to" if append else "Wrote"
        return f"Success: {action} '{file_path}' ({line_count} lines this call, {size:,} bytes total on disk)."
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def read_file(file_path: str, max_lines: int = 0) -> str:
    """Read and return the contents of a file (UTF-8).
    For very large files, set max_lines to limit how many lines are returned
    (e.g. max_lines=200). max_lines=0 (default) returns the whole file."""
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist."
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            if max_lines and max_lines > 0:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line)
                return "".join(lines) + f"\n... [truncated at {max_lines} lines]"
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"
