import sys
import time
import json

from colorama import Fore
import log_analysis

def json_load(file):
    with open(file, 'r') as f:
        return json.load(f)

def run_scan(log_file):
    logs = json_load(log_file)
    triggers = json_load("trigger.json")
    for entry in logs:
        for trig in triggers:
            try:
                if eval(compile(trig["condition"], "<string>", "eval"), {}, {"log": entry}):
                    action = getattr(log_analysis, trig["action"], None)
                    if callable(action):
                        action(entry)
            except Exception as e:
                print(f"[ERROR] Trigger failed: {e}")
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
            for trig in triggers:
                try:
                    if eval(compile(trig["condition"], "<string>", "eval"), {}, {"log": new_entry}):
                        action = getattr(log_analysis, trig["action"], None)
                        if callable(action):
                            action(new_entry)
                except Exception as e:
                    print(f"[ERROR] Trigger failed: {e}")
            old_len = len(new_logs)
            print("[INFO] New entry processed.\n")

if __name__ == "__main__":
    mode = sys.argv[1]
    filename = sys.argv[2]

    if mode == "scan":
        run_scan(filename)
    elif mode == "watch":
        run_watch(filename)
    else:
        print("Invalid mode. Use 'scan' or 'watch'.")