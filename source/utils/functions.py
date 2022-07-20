from pathlib import Path

from core import Asteroid

__all__ = ["load_extensions"]


def load_extensions(client: Asteroid, path: str):
    path = Path(path)
    for extension in path.iterdir():
        name = extension.name
        if name == "__pycache__":
            continue
        if name.endswith(".py"):
            client.load(f"{path}.{name[:-3]}")
        elif extension.is_dir():
            client.load(f"{path}.{name}")
