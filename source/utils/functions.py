from pathlib import Path

from core import Asteroid

__all__ = ["load_extensions"]


def load_extensions(client: Asteroid, path: str):
    path = Path(path)
    for extension in path.iterdir():
        name = extension.name
        if name.endswith(".py"):
            client.load(name[:2])
        if extension.is_dir():
            client.load(name)
