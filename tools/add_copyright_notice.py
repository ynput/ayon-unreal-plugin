# -*- coding: utf-8 -*-
"""Simple script to check for copyright notice.

 This is simple script to modify or check source files
 for commented copyright notice to comply with Epic
 Marketplace rules.

"""
import os
import re
from pathlib import Path

comments = re.compile(r"^//|#")
copyright_notice = re.compile(r"(?://|#) Copyright \(c\) (\d+) Ynput s\.r\.o\.")

supported_exts = [".cpp", ".hpp", ".cs", ".h", ".cc", ".c", ".py"]
current_path = Path.cwd()

print("*** Check commented copyright notice on the sources.")
print("    This will run in current directory, and in UE_* sub-folders. ")
current_dir_message = f">>> Current dir: {current_path.as_posix()}"
print(current_dir_message)
print("-" * len(current_dir_message))

def _scan_hierarchy(path):
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from _scan_hierarchy(entry.path)
        else:
            yield entry


def has_copyright_comment(file):
    with open(file, "r") as f:
        line = f.readline().strip()
        if not re.match(copyright_notice, line):
            print(f"!!! Missing or invalid copyright notice.\n  - {file}")
            print(line)
            print("^" * len(line))
            return


for entry in os.scandir(current_path):
    if entry.is_dir() and not entry.name.startswith("UE_"):
        continue
    if entry.is_file():
        continue
    for ue_entry in _scan_hierarchy(entry.path):
        if ue_entry.is_file() and Path(ue_entry.path).suffix in supported_exts:
            has_copyright_comment(ue_entry.path)
