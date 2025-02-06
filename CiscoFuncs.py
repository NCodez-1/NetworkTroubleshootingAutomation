from collections import deque
from math import ceil
import json
from netmiko import ConnectHandler
from datetime import datetime
import time
from colorama import Fore, Style, init
import structlog
import logging
import os

log_file_path = "NetworkLogs.json"
init(autoreset=True)

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


def list_devices():
    file = "Devices.json"

    print(Fore.GREEN + "List of devices on the network:")

    try:
        with open(file, 'r') as devices:
            data = json.load(devices)  
            for device_name, device_info in data.items():  
                ip_address = device_info.get("host", "Unknown") 
                print(Fore.GREEN + f"{device_name} - {ip_address}")  
    except json.JSONDecodeError as e:
        print(Fore.RED + f"Error decoding JSON: {e}")
    except FileNotFoundError:
        print(Fore.RED + "Error: Devices.json not found.")


def load_devices():
    file = "Devices.json"
    try:
        with open(file, 'r') as devices:
            return json.load(devices) 
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(Fore.RED + f"Error loading devices: {e}")
        return {}
    

def select_device():
    devices = load_devices()
    if not devices:
        print(Fore.RED + "No devices found.")
        return

    print(Fore.GREEN + "Available devices:")
    for index, device in enumerate(devices.keys(), start=1):
        print(Fore.YELLOW + f"{index}. {device}")

    while True:
        try:
            choice = int(input(Fore.GREEN + "Select a device (number): "))
            selected_device = list(devices.keys())[choice - 1]  
            break  
        except (ValueError, IndexError):
            print(Fore.RED + "Invalid selection. Please enter a valid number.")

    cisco_device = devices[selected_device]
    return cisco_device


def check_interfaces(cisco_device):
    

    try:
        connection = ConnectHandler(**cisco_device)
        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command("show ip interface brief")
        print(f"interface Status\n{output}")
        connection.disconnect()

    except Exception as e:
        print(f"Error {e}")


def show_vlan_brief(cisco_device):
    try:
        connection = ConnectHandler(**cisco_device)
        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command("show vlan brief")
        print(f"Vlan Brief\n{output}")
        connection.disconnect()
    except Exception as e:
        print(f"Error {e}")


def log_interface(cisco_device):
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


def logs(number):

    file = "NetworkLogs.json"

    with open(file, 'r') as log:
        last_lines = deque(log, maxlen=number)

    for line in last_lines:
        try:
            data = json.loads(line)
            print(data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")


def add_devices():

    json_file = "Devices.json"

    host = input(Fore.GREEN + "Enter host address: ")
    username = input(Fore.GREEN + "Enter username: ")
    password = input(Fore.GREEN + "Enter password: ")
    secret = input(Fore.GREEN + "Enter secret: ")
    device_name = input(Fore.GREEN + "Enter the device name: ")
    
    new_device = {
        "device_type": "cisco_ios",
        "host": host,
        "username": username,
        "password": password,
        "port": "22",
        "secret": secret
    }
    
    try:
        with open(json_file, "r") as file:
            devices = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        devices = {}

    devices[device_name] = new_device

    with open(json_file, "w") as file:
        json.dump(devices, file, indent=4)

    print(Fore.GREEN + f"Device {device_name} added")

