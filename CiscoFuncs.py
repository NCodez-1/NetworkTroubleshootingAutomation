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
import openai

def ai_prompt():
    api_key = ""
    base_url = "https://api.aimlapi.com/v1"
    model = "gpt-4o"

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    user_input = input("Enter your Rule: ")

    full_prompt = """
        {
            "instructions": "You are an AI assistant that generates Python log filtering rules. You must ONLY output a single Python line in this format:\n\nrulebook.add_rule(lambda log: ...)\n\nUse the user's request to build the rule. Do NOT include explanations, summaries, JSON, or anything else. Just return the Python line that fulfills the request below.",



            "example_log": {
                "timestamp": "2025-04-25T09:20:11Z",
                "device_name": "edge-router-02",
                "severity": "CRITICAL",
                "event": "BGP_PEER_DOWN",
                "status": "down",
                "message": "BGP peer 192.168.200.1 on ASN 65001 went down",
                "peer_ip": "192.168.200.1",
                "asn": 65001
            },

            "example_rule": {
                "rule_response": "rulebook.add_rule(lambda log: log.get('severity') == 'CRITICAL')"
            },

            "user_request": {
                "description": "{user_input}"
            }
        }
        """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )

        print("AI Response:", response.choices[0].message.content)
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


#creates a list of all devices on the network and their address
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


#simular function to be called within the next
def load_devices():
    file = "Devices.json"
    try:
        with open(file, 'r') as devices:
            return json.load(devices) 
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(Fore.RED + f"Error loading devices: {e}")
        return {}
    

""" When multiply network devices have been added to the topology this allows specific devies to be chosen to SSH into and run 
    troubleshooting commands. for automated purposes this can be added into a script which chooses devices automatically """
    
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


#SSH into the chosen device and shows interface brief
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

