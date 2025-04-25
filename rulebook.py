import json
import time
from typing import Callable, List, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

LogEntry = Dict[str, any]
Rule = Callable[[LogEntry], bool]

class RuleBook:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.rules: List[Rule] = []
        self.last_seen_log_count = 0

    def add_rule(self, rule: Rule):
        self.rules.append(rule)

    def load_logs(self) -> List[LogEntry]:
        with open(self.log_file, 'r') as f:
            return json.load(f)

    def check_new_logs(self):
        logs = self.load_logs()
        new_logs = logs[self.last_seen_log_count:]
        self.last_seen_log_count = len(logs)

        for log in new_logs:
            for rule in self.rules:
                if rule(log):
                    self.trigger(log)

    def trigger(self, log: LogEntry):
        print(f"Triggered on log from {log.get('device_name', 'unknown')} — Event: {log.get('event_type')} — Severity: {log.get('severity')}")

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, rulebook: RuleBook):
        self.rulebook = rulebook

    def on_modified(self, event):
        if event.src_path.endswith(self.rulebook.log_file):
            print(f"Detected update to {self.rulebook.log_file}")
            self.rulebook.check_new_logs()

if __name__ == "__main__":
    log_file = "example.json"
    rulebook = RuleBook(log_file)

    # Add rules
    rulebook.add_rule(lambda log: log.get("severity") == "CRITICAL")
    rulebook.add_rule(lambda log: log.get("status") == "flapping")
    rulebook.add_rule(lambda log: log.get("latency_ms", 0) > 100)
    rulebook.add_rule(lambda log: float(log.get("packet_loss", "0%").strip('%')) > 10)

    # Initial load to set log count
    rulebook.load_logs()
    rulebook.last_seen_log_count = len(rulebook.load_logs())

    # Set up watchdog
    event_handler = LogFileHandler(rulebook)
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()

    print(f" Watching {log_file} for updates...")
