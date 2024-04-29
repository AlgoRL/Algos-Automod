import os
import utils

all_files = [
    "./assets",
    "./core",
    "./core/main.py",
    "./core/prereqs.py",
    "./core/report.py",
    "./core/utils.py",
    "./data",
    "./data/guild_data.json",
    "./data/user_data.json"
]

required_files = [
    "./core",
    "./core/main.py",
    "./core/prereqs.py",
    "./core/report.py",
    "./core/utils.py",
    "./data",
    "./data/guild_data.json",
    "./data/user_data.json"
]

def files_present():
    for path in required_files:
        if not os.path.exists(path):
            utils.fatal("FILE ERROR", f"File: `{path}` not found.")
            return False
    utils.log_process("UTIL", "File existence verified...")
    return True