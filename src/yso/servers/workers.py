import dataclasses
import pathlib
import re
import subprocess

from fastapi import FastAPI, Response


@dataclasses.dataclass
class Block:
    name: str
    content: str
    line_start: int
    line_end: int


def create_worker_server() -> FastAPI:
    app = FastAPI()
    path_ = pathlib.Path(".")

    @app.get("/")
    async def index() -> str:
        return "index"

    @app.get("/path")
    async def path() -> str:
        return str(path_.resolve())

    @app.get("/chunk_main_file")
    async def chunk_main_file():
        path_file = path_ / "_main.py"

        if not path_file.exists():
            return Response(status_code=404)

        with path_file.open() as fd:
            text = fd.readlines()

        blocks: list[Block] = []
        current_block_name: str | None = None
        current_content = []
        rgx_block_begin = re.compile(r"# BEGIN \[[^\]]+\]")
        rgx_block_end = re.compile(r"# END")

        for line in text:
            match_ = rgx_block_begin.match(line)
            if match_:
                if current_content:
                    raise ValueError

                current_block_name = match_.groups()[0]
                continue

            match_ = rgx_block_end.match(line)
            if match_:
                if not current_block_name:
                    raise ValueError

                block = Block(
                    name=current_block_name,
                    content="\n".join(current_content),
                    line_start=0,
                    line_end=0,
                )
                blocks.append(block)
                current_block_name = None
                continue

            if current_block_name is not None:
                current_content.append(line)

        return blocks

    @app.get("/venv")
    async def venv() -> list[str]:
        result = subprocess.run(["uv", "pip", "freeze"], capture_output=True, text=True)
        return result.stdout.split("\n")

    return app
