from collections import deque
import inspect
from math import ceil
import json
from netmiko import ConnectHandler
from datetime import datetime
import time
from colorama import Fore, Style, init
import structlog
import logging
import os
import runbook
import runbook
import socket
import requests
import openai
import re

WEBEX_TOKEN = "YmI1YWIxNDAtNTM2NC00NzEwLThlZDEtNjU4NDU2ZThlNGI2NGRkZjFhYzQtM2Vm_PE93_551a1417-a6a5-47bb-8629-f1a6cba62826"
ROOM_ID = "e0cc9f30-edfd-11ef-8a04-05a7fd281849"

init(autoreset=True)

api_key = ""
API_KEY_FILE = "api_key.txt"

def load_api_key():
    global api_key
    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as f:
            api_key = f.read().strip()

def save_api_key():
    with open(API_KEY_FILE, "w") as f:
        f.write(api_key)

def set_api_key(new_key):
    global api_key
    api_key = new_key
    save_api_key()

def get_api_key():
    return api_key

def create_trigger_with_ai():
    base_url = "https://api.aimlapi.com/v1"
    model = "gpt-4o"

    client = openai.OpenAI(api_key=get_api_key(), base_url=base_url)

    user_input = input("Describe the trigger you want to create: ")

    full_prompt = f"""
        You are an AI assistant that generates Python log filtering trigger.

        Only respond with a single line of Python code in the following format:
        "log.get('packet_loss') and int(log['packet_loss'].replace('%', '')) > 10",

        Do not include explanations, formatting, or any other content.

        Use this sample log to understand the context:

        {{
        "timestamp": "2025-04-25T09:20:11Z",
        "device_name": "edge-router-02",
        "severity": "CRITICAL",
        "event": "BGP_PEER_DOWN",
        "status": "down",
        "message": "BGP peer 192.168.200.1 on ASN 65001 went down",
        "peer_ip": "192.168.200.1",
        "asn": 65001
        }}

        Respond to this user description:
        \"{user_input}\"
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.2,
            max_tokens=100,
        )

        raw_condition = response.choices[0].message.content.strip()
        clean_condition = re.sub(r"```(?:python)?\n?([\s\S]+?)\n?```", r"\1", raw_condition).strip()
        condition = clean_condition
        print("\nAI-generated condition:")
        print(f"    {condition}")

        print("\nAvailable action functions from runbook.py:")
        actions = list(runbook.events_and_actions.keys())
        for i, action in enumerate(actions, 1):
            print(f"  [{i}] {action}")

        while True:
            try:
                selection = int(input("Choose an action by number: "))
                if 1 <= selection <= len(actions):
                    selected_key = actions[selection - 1]
                    action_name = runbook.events_and_actions[selected_key].__name__
                    break
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")

        trigger_entry = {"condition": condition, "action": action_name}
        try:
            with open("trigger.json", "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        data.append(trigger_entry)

        with open("trigger.json", "w") as f:
            json.dump(data, f, indent=4)

        print(f"\nTrigger saved! Condition will trigger '{action_name}'.")

    except Exception as e:
        print(f"Error communicating with AI API: {e}")



#folder locations in directory
log_file_path = "NetworkLogs.json"

#resets text color after each line
init(autoreset=True)

#get log information net netmiko
logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("netmiko").setLevel(logging.WARNING)

#format for the log to created
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(message)s",
    filemode="a",
)

#structure of the log data in json
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

#creates variable for the logs
log = structlog.get_logger()


#list all devices in the program eg Switch1, Router1 etc
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


#loads a chosen device
def load_devices():
    file = "Devices.json"
    try:
        with open(file, 'r') as devices:
            return json.load(devices) 
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(Fore.RED + f"Error loading devices: {e}")
        return {}
    

#user selection for network devices, loads a list of whats in the program then loads the deatils to be used in SSH functions
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

""" ------------------------- Start of cisco commands for trouble shooting -------------------------

    These all use the cisco_device variabel loaded from the previous functions to SSH into the
    device then runs the cisco command"""

#SSH into the chosen device and shows interface brief
def check_interfaces(cisco_device):
    try:
        connection = ConnectHandler(**cisco_device)
        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command("show ip interface brief")
        print(f"Interface Status:\n{output}")
        connection.disconnect()


    except Exception as e:
        print(f"Error {e}")

#SSH into device and shows vlan brief 
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

""" ------------------------- end of cisco commands for trouble shooting -------------------------"""

""" This allows the returned information from the command to log the results as it comes from the terminal
    it checks for strings in the returned output to log if the interface is up or down and uses the logging
    structure from the beggining of the program to return it in a JSON file """ 
    
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

#prints content of the network logs
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

""" To be able to SSH into devices on the network to run cisco commands and check their status each device needs its credentials
    in the program so it can automatically access them, ths function simplifies having to hard code in each device
    in the network topology and then formats the credentials into a JSON file which the program can extract
    the details needed to access the device """

# Function to add new devices to the program, devices for this use same credentials so only device IP needs to be inputted
def add_devices():

    json_file = "Devices.json"

    host = input(Fore.GREEN + "Enter host address: ")
    device_name = input(Fore.GREEN + "Enter the device name: ")
    
    new_device = {
        "device_type": "cisco_ios",
        "host": host,
        "username": "admin",
        "password": "cisco",
        "port": "22",
        "secret": "secret"
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

"""------------------------------------Functions to send logging messages to Webex room------------------------------------"""

def send_to_webex(message):
    url = "https://webexapis.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {WEBEX_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "roomId": ROOM_ID,
        "text": message
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Failed to send message: {response.status_code} {response.text}")


def start_syslog_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 9002))
    print("Listening for syslog messages...")
    while True:
        data, addr = sock.recvfrom(4096)
        message = data.decode()
        print(f"Received from {addr}: {message}")
        send_to_webex(message)

"""----------------------------------------------------End of logs----------------------------------------------------"""

load_api_key()