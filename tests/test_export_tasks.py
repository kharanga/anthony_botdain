import json
import os
import subprocess
import sys
from pathlib import Path

EXPORT_TASKS_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "export_tasks.py"


def issue(number, title, body):
    return {
        "number": number,
        "title": title,
        "body": body,
        "state": "open",
        "labels": [],
        "html_url": f"https://github.com/kharanga/anthony_botdain/issues/{number}",
    }


def write_fake_gh(bin_dir: Path, replies_by_api_path: dict) -> None:
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    fake_gh.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        f"replies = json.loads({json.dumps(json.dumps(replies_by_api_path))})\n"
        "print(json.dumps(replies[sys.argv[2]]))\n"
    )
    fake_gh.chmod(0o755)


def run_export(tmp_path: Path, replies_by_api_path: dict) -> subprocess.CompletedProcess:
    bin_dir = tmp_path / "bin"
    write_fake_gh(bin_dir, replies_by_api_path)
    environment = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(
        [sys.executable, str(EXPORT_TASKS_SCRIPT), str(tmp_path / "task"), str(tmp_path / "archived")],
        env=environment,
        capture_output=True,
        text=True,
    )


def test_issues_with_no_body_and_a_title_without_a_colon_are_exported(tmp_path):
    replies = {
        "repos/kharanga/anthony_botdain/issues/1/sub_issues?per_page=100": [issue(40, "Loose task", None)],
        "repos/kharanga/anthony_botdain/issues/40/sub_issues?per_page=100": [issue(41, "A ticket", None)],
    }

    result = run_export(tmp_path, replies)

    assert result.returncode == 0, result.stderr
    exported_files = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.glob("task/*/*.md"))
    assert exported_files == ["task/loose-task/41-a-ticket.md", "task/loose-task/task.md"]
    assert "# #40: Loose task" in (tmp_path / "task" / "loose-task" / "task.md").read_text()
