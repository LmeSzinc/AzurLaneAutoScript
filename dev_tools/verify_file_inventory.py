"""Final delivery check: file inventory comparison master vs refactor branch."""

import subprocess

master_files = subprocess.run(
    ["git", "ls-tree", "-r", "--name-only", "master"], capture_output=True, text=True, check=True
).stdout.splitlines()
branch_files = subprocess.run(
    ["git", "ls-tree", "-r", "--name-only", "HEAD"], capture_output=True, text=True, check=True
).stdout.splitlines()
m_py = {f for f in master_files if f.endswith(".py")}
b_py = {f for f in branch_files if f.endswith(".py")}
deleted = m_py - b_py
added = b_py - m_py
print(f"master .py files: {len(m_py)}, branch .py files: {len(b_py)}")
print(f"deleted files: {sorted(deleted) if deleted else 'NONE'}")
print(f"added files: {len(added)}")
for f in sorted(added):
    print("  +", f)
