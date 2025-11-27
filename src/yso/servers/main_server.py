import dataclasses
import functools
import multiprocessing
import pathlib
import signal
import sys
from typing import Any

import pydantic
from fastapi import FastAPI, Response

from servebook.servers.utils import spawn_worker
from servebook.utils.server import get_free_port


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
class Project:
    path: pathlib.Path
    port: int
    process: multiprocessing.Process


def shutdown_servers(project_map: dict[Any, Project], sig, frame):
    print("\nShutting down servers...")
    for project in project_map.values():
        project.process.terminate()

    for project in project_map.values():
        project.process.join(timeout=5)

    sys.exit(0)


class SpawnBody(pydantic.BaseModel):
    path: pathlib.Path


class StopBody(pydantic.BaseModel):
    path: pathlib.Path


def create_main_server(path_dir: pathlib.Path | str) -> FastAPI:
    path = _convert_path(path_dir)
    current_id = 0
    project_map: dict[int, Project] = {}

    signal_handler = functools.partial(shutdown_servers, project_map=project_map)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    app = FastAPI()

    @app.get("/")
    def index() -> str:
        return "Hello World!"

    @app.get("/servers")
    def servers() -> dict[int, Project]:
        return {k: v for k, v in project_map.items()}

    @app.get("/projects")
    def projects() -> list[str]:
        return [str(p.resolve()) for p in path.iterdir() if _is_project_dir(p)]

    @app.post("/worker/spawn")
    def post_spawn_server(body: SpawnBody):
        nonlocal current_id

        port = get_free_port()
        p = multiprocessing.Process(target=spawn_worker, args=(body.path, port))
        p.start()

        current_id += 1
        project_map[current_id] = Project(path=body.path, port=port, process=p)
        print(f"Started server for {body.path} on port {port}")

        return Response(status_code=200)

    @app.post("/worker/{id}/stop")
    def post_stop_server(id: int):
        try:
            project = project_map.pop(id)
            project.process.terminate()
            print(f"Stopped the server {id} running on port {project.port}")
            return Response(status_code=200)

        except KeyError:
            return Response(status_code=404)

    return app
