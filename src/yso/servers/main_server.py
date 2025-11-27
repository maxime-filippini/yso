import functools
import multiprocessing
import pathlib
import signal
import sys

import httpx
import pydantic
from fastapi import FastAPI, Response
from pydantic import dataclasses

from yso.servers.utils import spawn_worker
from yso.utils.server import get_free_port


def _convert_path(path: pathlib.Path | str) -> pathlib.Path:
    if isinstance(path, pathlib.Path):
        return path
    return pathlib.Path(path)


def _is_project_dir(path: pathlib.Path):
    if not path.is_dir():
        return False

    if not (path / "uv.lock").exists():
        return False

    return True


@dataclasses.dataclass
class ProjectInfo:
    path: pathlib.Path
    port: int

    @property
    def url(self):
        return f"http://localhost:{self.port}"


type ProjectMap = dict[int, tuple[multiprocessing.Process, ProjectInfo]]


def shutdown_servers(project_map: ProjectMap, sig, frame):
    print("\nShutting down servers...")
    for process, _ in project_map.values():
        process.terminate()

    for process, _ in project_map.values():
        process.join(timeout=5)

    sys.exit(0)


class SpawnBody(pydantic.BaseModel):
    path: pathlib.Path


class StopBody(pydantic.BaseModel):
    path: pathlib.Path


def create_main_server(path_dir: pathlib.Path | str) -> FastAPI:
    # path = _convert_path(path_dir)
    current_id = 0
    project_map: dict[int, tuple[multiprocessing.Process, ProjectInfo]] = {}

    signal_handler = functools.partial(shutdown_servers, project_map=project_map)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = FastAPI()

    @app.get("/")
    def index() -> str:
        return "Hello World!"

    @app.get("/servers")
    def servers() -> dict[int, int]:
        return {k: v.port for k, (_, v) in project_map.items()}

    # @app.get("/projects")
    # def projects() -> list[str]:
    #     return [str(p.resolve()) for p in path.iterdir() if _is_project_dir(p)]

    @app.post("/worker/spawn")
    def post_spawn_server(body: SpawnBody) -> Response:
        nonlocal current_id

        port = get_free_port()
        p = multiprocessing.Process(target=spawn_worker, args=(body.path, port))
        p.start()

        current_id += 1
        project_map[current_id] = p, ProjectInfo(path=body.path, port=port)
        print(f"Started server for {body.path} on port {port}")

        return Response(status_code=200)

    @app.post("/worker/{id}/stop")
    def post_stop_server(id: int) -> Response:
        try:
            process, project_info = project_map.pop(id)
            process.terminate()
            print(f"Stopped the server {id} running on port {project_info.port}")
            return Response(status_code=200)

        except KeyError:
            return Response(status_code=404)

    @app.post("/worker/{id}/process")
    def process_main_file(id: int):
        try:
            _, project_info = project_map[id]
        except KeyError:
            return Response(status_code=404)

        with httpx.Client() as client:
            res = client.post(f"{project_info.url}/process-main-file")

        return res.json()

    return app
