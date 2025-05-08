import json
import time
import os
import importlib
import runbook

TRIGGER_FILE = "trigger.json"
LOG_FILE = "example.json"
LAST_LINE_FILE = ".last_processed"

# Load triggers and associated action functions
def load_triggers():
    with open(TRIGGER_FILE, "r") as f:
        return json.load(f)

# Load logs and return only new entries
def get_new_logs():
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

    last_ts = None
    if os.path.exists(LAST_LINE_FILE):
        with open(LAST_LINE_FILE, "r") as f:
            last_ts = f.read().strip()

    if not last_ts:
        return [logs[-1]] if logs else []

    new_logs = [log for log in logs if log["timestamp"] > last_ts]
    return new_logs

# Save timestamp of last processed log
def update_last_processed(log):
    with open(LAST_LINE_FILE, "w") as f:
        f.write(log["timestamp"])

# Evaluate trigger condition and run associated action
def process_log(log_entry, triggers):
    for trigger in triggers:
        try:
            condition_code = compile(trigger["condition"], "<string>", "eval")
            if eval(condition_code, {}, {"log": log_entry}):
                action_name = trigger["action"]
                action_func = getattr(runbook, action_name, None)
                if callable(action_func):
                    print(f"[INFO] Trigger matched. Running action: {action_name}")
                    action_func(log_entry)
                else:
                    print(f"[ERROR] Action '{action_name}' not found in log_analysis.py.")
        except Exception as e:
            print(f"[ERROR] Failed to process trigger: {e}")

def main_loop(poll_interval=5):
    print("[INFO] Trigger engine started. Monitoring logs...")
    while True:
        triggers = load_triggers()
        new_logs = get_new_logs()
        for log_entry in new_logs:
            process_log(log_entry, triggers)
            update_last_processed(log_entry)
        time.sleep(poll_interval)

if __name__ == "__main__":
    main_loop()