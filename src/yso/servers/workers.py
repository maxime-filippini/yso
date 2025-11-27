import pathlib
import subprocess

from fastapi import FastAPI, Response

from yso.parse.yso_file import extract_blocks


def create_worker_server() -> FastAPI:
    app = FastAPI()
    path_ = pathlib.Path(".")

    @app.get("/")
    async def index() -> str:
        return "index"

    @app.get("/path")
    async def path() -> str:
        return str(path_.resolve())

    @app.post("/process-main-file")
    async def process_main_file():
        path_file = path_ / "_main.py"

        if not path_file.exists():
            return Response(status_code=404)

        with path_file.open() as fd:
            text = fd.read()

        blocks = extract_blocks(text)

        return blocks

    @app.get("/venv")
    async def venv() -> list[str]:
        result = subprocess.run(["uv", "pip", "freeze"], capture_output=True, text=True)
        return result.stdout.split("\n")

    return app
