from collections import deque
from math import ceil
import json
from netmiko import ConnectHandler
from datetime import datetime
import time
from colorama import Fore, Style
import structlog
import logging
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(project_dir, "NetworkLogs.json")

logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("netmiko").setLevel(logging.WARNING)

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(message)s",
    filemode="a",
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()

cisco_device = {
    'device_type': 'cisco_ios',
    'host': '##########',
    'username': '#####',
    'password': '#####',
    'port': ####,
    'secret': '#####'}


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
    if_name = input("Select an interface to check: ")

    try:
        connection = ConnectHandler(**cisco_device)
        connection.enable()

        output = connection.send_command(f"show interface {if_name} status")
        connection.disconnect()

        if "notconnect" in output:
            log.error(
                "Interface Down",
                interface=if_name,
                status="Not Connected",
                device=cisco_device["host"],
            )
        else:
            log.info(
                "Interface is up",
                interface=if_name,
                status="Connected",
                device=cisco_device["host"],
            )

    except Exception as e:
        log.error("Error checking interface", error=str(e))

    print(f"Logs saved to: {log_file_path}")


def Logs(number):

    files = [
        file for file in os.listdir(project_dir)
        if file.endswith('.json')
    ]
    print("Log file:", files)

    file = 'NetworkLogs.json'

    with open(file, 'r') as log:
        last_lines = deque(log, maxlen=number)

    for line in last_lines:
        try:
            data = json.loads(line)
            print(data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
