import pathlib

import click
import uvicorn

from yso.servers.main_server import create_main_server
from yso.servers.workers import create_worker_server


@click.group()
def cli():
    pass


def _init_directory(path: pathlib.Path) -> None:
    path_dir = path / ".yso"

    if not path_dir.exists():
        path_dir.mkdir()


@cli.command()
@click.argument("path")
def serve(path: str | None = None):
    if path is None:
        path = "."

    app = create_main_server(path)
    uvicorn.run(app, port=8000)


@cli.command()
@click.argument("port")
def spawn(port: int):
    app = create_worker_server()
    uvicorn.run(app, port=int(port))
