import pathlib
import subprocess


# TODO - Make more robust
def check_if_path_is_valid_package(path: pathlib.Path):
    has_pyproject = (path / "pyproject.toml").exists()
    has_uv = (path / "uv.lock").exists()

    return has_pyproject and has_uv


def spawn_worker(path: pathlib.Path, port: int):
    subprocess.call(["uv", "run", "yso", "spawn", str(port)], cwd=path)
