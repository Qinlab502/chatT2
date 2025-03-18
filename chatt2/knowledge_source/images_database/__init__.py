from pathlib import Path

root = Path(__file__) / ".."
cwd = Path.cwd()

dynamic_images_cache_path = (root / "dynamic").resolve().relative_to(cwd).as_posix() + "/"
static_images_cache_path = (root / "static").resolve().relative_to(cwd).as_posix() + "/"
