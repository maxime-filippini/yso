import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any


class BasedPyrightCLI:
    @staticmethod
    async def get_diagnostics(
        code: str, filename: str = "notebook.py"
    ) -> list[dict[str, Any]]:
        """Run basedpyright CLI and return diagnostics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / filename
            file_path.write_text(code)

            # Run basedpyright with JSON output
            process = await asyncio.create_subprocess_exec(
                "basedpyright",
                "--outputjson",
                str(file_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmpdir,
            )

            stdout, stderr = await process.communicate()

            if stdout:
                result = json.loads(stdout.decode("utf-8"))

                diagnostics = []
                for diag in result.get("generalDiagnostics", []):
                    severity_map = {"error": 1, "warning": 2, "information": 3}

                    diagnostics.append(
                        {
                            "severity": severity_map.get(
                                diag.get("severity", "error"), 1
                            ),
                            "message": diag.get("message", ""),
                            "range": {
                                "start": {
                                    "line": diag.get("range", {})
                                    .get("start", {})
                                    .get("line", 0),
                                    "character": diag.get("range", {})
                                    .get("start", {})
                                    .get("character", 0),
                                },
                                "end": {
                                    "line": diag.get("range", {})
                                    .get("end", {})
                                    .get("line", 0),
                                    "character": diag.get("range", {})
                                    .get("end", {})
                                    .get("character", 0),
                                },
                            },
                            "code": diag.get("rule"),
                            "source": "basedpyright",
                        }
                    )

                return diagnostics

            return []


code = """

def f(a: int) -> int:
    return 2.2

"""

print(asyncio.run(BasedPyrightCLI.get_diagnostics(code)))
