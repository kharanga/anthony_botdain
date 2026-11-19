import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = "kharanga/anthony_botdain"
SPEC_ISSUE = 1
active_root = Path(sys.argv[1])
archive_root = Path(sys.argv[2])

def gh_json(path):
    output = subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout
    return json.loads(output)

def slug_from_title(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

def task_folder_name(title):
    task_code, colon, task_name = title.partition(":")
    if not colon:
        return slug_from_title(title)
    return f"{task_code.strip()}-{slug_from_title(task_name)}"

def markdown_for_issue(issue, parent_number):
    labels = ", ".join(label["name"] for label in issue["labels"]) or "none"
    parent_line = f"**Parent:** #{parent_number}  \n" if parent_number else ""
    return f"""# #{issue['number']}: {issue['title']}

{parent_line}**Status:** {issue['state']}  
**Labels:** {labels}  
**GitHub:** {issue['html_url']}

{(issue['body'] or '').strip()}
"""

task_issues = gh_json(f"repos/{REPO}/issues/{SPEC_ISSUE}/sub_issues?per_page=100")
written = []
for task_issue in task_issues:
    folder_name = task_folder_name(task_issue["title"])
    task_is_finished = task_issue["state"] == "closed"
    task_folder = (archive_root if task_is_finished else active_root) / folder_name
    stale_folder = (active_root if task_is_finished else archive_root) / folder_name
    if stale_folder.exists():
        shutil.rmtree(stale_folder)
    task_folder.mkdir(parents=True, exist_ok=True)
    (task_folder / "task.md").write_text(markdown_for_issue(task_issue, SPEC_ISSUE))
    written.append(str(task_folder / "task.md"))
    for ticket_issue in gh_json(f"repos/{REPO}/issues/{task_issue['number']}/sub_issues?per_page=100"):
        ticket_path = task_folder / f"{ticket_issue['number']}-{slug_from_title(ticket_issue['title'])}.md"
        ticket_path.write_text(markdown_for_issue(ticket_issue, task_issue["number"]))
        written.append(str(ticket_path))

print("\n".join(sorted(written)))
