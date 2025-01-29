from netmiko import ConnectHandler
from datetime import datetime
import time
from colorama import Fore, Style
import structlog
import logging
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(project_dir, "network_troubleshooting.json")

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(message)s"
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()

cisco_device = {
    'device_type': 'cisco_ios',
    'host': '############',
    'username': '#####',
    'password': '######',
    'port': 22,
    'secret': '######'}


def check_interfaces():
    try:
        connection = ConnectHandler(**cisco_device)
        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command("show ip interface brief")
        print(f"interface Status\n{output}")
        connection.disconnect()

    except Exception as e:
        print(f"Error {e}")


def show_vlan_brief():
    try:
        connection = ConnectHandler(**cisco_device)
        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command("show vlan brief")
        print(f"Vlan Brief\n{output}")
        connection.disconnect()
    except Exception as e:
        print(f"Error {e}")


def log_interface():
    if_name = input("Select an interface: ")
    try:
        connection = ConnectHandler(**cisco_device)

        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command(f"show interface {if_name} status")
        print(f"\nInterface Status:\n{output}\n")

        if "notconnect" in output:
            log.error(
                "Interface Down",
                interface=if_name,
                status="Not Connected",
                device=cisco_device["host"]
            )
        elif "connected" in output:
            log.info(
                "Interface is up",
                interface=if_name,
                status="Connected",
                device=cisco_device["host"]
            )
        else:
            log.warning(
                "Unknown Interface Status",
                interface=if_name,
                output=output,
                device=cisco_device["host"]
            )

        connection.disconnect()

    except Exception as e:
        log.error("Connection failed", error=str(e), device=cisco_device["host"])
        print(f"Error: {e}")


if __name__ == "__main__":
    while True:
        print(f"[{datetime.now}] Connected to {cisco_device['host']}")
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        check_interfaces()
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        print(f"Waiting 10 seconds before next task")
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        time.sleep(10)
        show_vlan_brief()
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        log_interface()
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        print(f"[{datetime.now()}] Connection closed")
        break

