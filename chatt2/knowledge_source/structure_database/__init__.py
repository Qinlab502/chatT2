from pathlib import Path

root = Path(__file__) / ".."
cwd = Path.cwd()

structure_database_file = (
    "sqlite:///"
    + (root / "chat_t2_database_v4.db").resolve().relative_to(cwd).as_posix()
)
