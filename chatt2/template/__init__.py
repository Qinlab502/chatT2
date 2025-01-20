from pathlib import Path

from ..utils import read_json, read_text

root = Path(__file__) / ".."
cwd = Path.cwd()
sql_template = read_text((root / "sql.txt").resolve().relative_to(cwd).as_posix())
modify_sql_template = read_text((root / "modify_sql.txt").resolve().relative_to(cwd).as_posix())
fuzz_sql_template = read_text((root / "fuzz_sql.txt").resolve().relative_to(cwd).as_posix())
simple_answer_template = read_text((root / "simple_answer.txt").resolve().relative_to(cwd).as_posix())
function_calling_template = read_json((root / "function_calling.json").resolve().relative_to(cwd).as_posix())
function_calling_system_prompt = read_text((root / "function_calling_system_prompt.txt").resolve().relative_to(cwd).as_posix())
