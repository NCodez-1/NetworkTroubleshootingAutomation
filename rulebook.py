# rulebook.py

import json
import time
import os
from typing import Callable, List, Dict, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import log_analysis

LogEntry = Dict[str, any]
Rule = Callable[[LogEntry], bool]
Action = Callable[[LogEntry], None]
RuleWithAction = Tuple[Rule, Action]
RuleStore = Dict[str, str]  # {"rule": "<lambda code>", "action": "function_name"}

RULES_FILE = "rules.json"

class RuleBook:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.rules: List[RuleWithAction] = []
        self.last_seen_log_count = 0

    def add_rule(self, rule: Rule, action: Action, save: bool = True, rule_code: str = None, action_name: str = None):
        self.rules.append((rule, action))

        # Save rule to file if requested
        if save and rule_code and action_name:
            self.save_rule_to_file(rule_code, action_name)

    def save_rule_to_file(self, rule_code: str, action_name: str):
        rule_data = {"rule": rule_code, "action": action_name}

        if os.path.exists(RULES_FILE):
            try:
                with open(RULES_FILE, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = []
        else:
            data = []

        data.append(rule_data)

        with open(RULES_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    def load_rules_from_file(self):
        if not os.path.exists(RULES_FILE):
            return

        with open(RULES_FILE, 'r') as f:
            try:
                stored_rules: List[RuleStore] = json.load(f)
            except json.JSONDecodeError:
                print("Failed to load rules — invalid JSON format.")
                return

        for item in stored_rules:
            try:
                rule_code = item["rule"]
                action_name = item["action"]

                rule = eval(rule_code)
                action = getattr(log_analysis, action_name)

                self.add_rule(rule, action, save=False)
                print(f"Loaded rule: {rule_code} -> {action_name}")
            except Exception as e:
                print(f"Error loading rule: {item} — {e}")

    def load_logs(self) -> List[LogEntry]:
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def check_new_logs(self):
        logs = self.load_logs()
        new_logs = logs[self.last_seen_log_count:]
        self.last_seen_log_count = len(logs)

        for log in new_logs:
            for rule, action in self.rules:
                try:
                    if rule(log):
                        self.trigger(log, action)
                except Exception as e:
                    print(f"Error while applying rule: {e}")

    def trigger(self, log: LogEntry, action: Action):
        print(f"\nRule triggered for log from {log.get('device_name', 'unknown')}:")
        print(f"  Event: {log.get('event', 'N/A')} — Severity: {log.get('severity', 'N/A')}")
        try:
            action(log)
        except Exception as e:
            print(f"Error executing action: {e}")

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, rulebook: RuleBook):
        self.rulebook = rulebook

    def on_modified(self, event):
        if event.src_path.endswith(self.rulebook.log_file):
            print(f"\nDetected update to {self.rulebook.log_file}")
            self.rulebook.check_new_logs()

# Optional test run
if __name__ == "__main__":
    log_file = "example.json"
    rulebook = RuleBook(log_file)

    # Load saved rules
    rulebook.load_rules_from_file()

    # Initial log tracking
    rulebook.load_logs()
    rulebook.last_seen_log_count = len(rulebook.load_logs())

    # Watch for updates
    event_handler = LogFileHandler(rulebook)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()

    print(f"Watching {log_file} for updates...\nPress Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("👋 Exiting.")
    observer.join()