import json
import time
import os
import importlib
import textwrap
import runbook

from colorama import Fore, Style, init
from runbook import events_and_actions

init(convert=True, autoreset=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TRIGGER_FILE = os.path.join(BASE_DIR, "trigger.json")
LOG_FILE = os.path.join(BASE_DIR, "example.json")
LAST_LINE_FILE = os.path.join(BASE_DIR, ".last_processed")

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
    triggered_conditions = []
    trigger_errors = []
    actions_run = []

    for trigger in triggers:
        try:
            condition_str = trigger["condition"]
            action_name = trigger["action"]
            rule_func = eval(f"lambda log: {condition_str}")
            if rule_func(log_entry):
                triggered_conditions.append(condition_str)
                action_func = getattr(runbook, action_name, None)
                if callable(action_func):
                    try:
                        action_func(log_entry)
                        actions_run.append(action_name)
                    except Exception as action_err:
                        trigger_errors.append(f"{action_name}() {str(action_err)}")
                else:
                    trigger_errors.append(f"[Action Not Found] {action_name}")
        except Exception as rule_err:
            trigger_errors.append(f"[Invalid rule] {trigger}: {rule_err}")

    if triggered_conditions:
        print(Fore.RED + "\n[ERROR] Trigger:" + Style.RESET_ALL)
        print(Fore.YELLOW + f"        Trigger count: {len(triggered_conditions)}" + Style.RESET_ALL)
        for cond in triggered_conditions:
            print(f'                "{cond}"')

        if trigger_errors:
            print(Fore.YELLOW + "        [Trigger-ERROR]" + Style.RESET_ALL)
            for err in trigger_errors:
                print(f"                {err}")

        if actions_run:
            print(Fore.CYAN + "        [Trigger-Action]" + Style.RESET_ALL)
            for action in actions_run:
                print(f"                ACTION: {action} triggered")

        # Pretty print the log entry
        print(Fore.YELLOW + "        Log:" + Style.RESET_ALL)
        formatted_log = json.dumps(log_entry, indent=4)
        print(textwrap.indent(formatted_log, "                "))

    print("\n" + Style.RESET_ALL)


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