import os
import sys
import time
import json

from colorama import Fore, Style, init
import runbook
import triggerbook

init(convert=True, autoreset=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def json_load(filename):
    path = os.path.join(BASE_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_scan(log_file):
    logs = json_load(log_file)
    triggers = json_load("trigger.json")
    for entry in logs:
        triggerbook.process_log(entry, triggers)
    print(Fore.GREEN + "\nFull scan completed.")

def run_watch(log_file):
    print(f"Watching {log_file} for new entries (Ctrl+C to stop)...")
    old_logs = json_load(log_file)
    old_len = len(old_logs)
    while True:
        time.sleep(1)
        new_logs = json_load(log_file)
        if len(new_logs) > old_len:
            new_entry = new_logs[-1]
            triggers = json_load("trigger.json")
            triggerbook.process_log(new_entry, triggers)
            old_len = len(new_logs)

if __name__ == "__main__":
    mode = sys.argv[1]
    filename = sys.argv[2]

    if mode == "scan":
        run_scan(filename)
    elif mode == "watch":
        run_watch(filename)
    else:
        print("Invalid mode. Use 'scan' or 'watch'.")