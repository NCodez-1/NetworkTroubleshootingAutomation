from collections import deque
from math import ceil
import json
from netmiko import ConnectHandler
import time
from colorama import Fore, Style, init
from elasticsearch import Elasticsearch
from datetime import datetime, timedelta



init(autoreset=True)

#sets Elasticsearch host
es_host = "http://localhost:9200"



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



# Querys Elasticsearch for recent logs from specific device chosen 
def query_recent_logs(es_host, device_ip):

    es = Elasticsearch(es_host)

    time.sleep(5)

    now = datetime.utcnow()
    past = now - timedelta(seconds=15)

    query = {
        "bool": {
            "must": [
                {"match": {"host.ip": device_ip}}, 
            ],
            "filter": [
                {
                    "range": {
                        "@timestamp": {
                            "gte": past.isoformat(),
                            "lte": now.isoformat()
                        }
                    }
                }
            ]
        }
    }

    response = es.search(index="filebeat-*", query=query, size=10)
    hits = response["hits"]["hits"]

    print(f"\n🔍 Recent logs from {device_ip}:\n")
    for hit in hits:
        print(hit["_source"]["message"])
