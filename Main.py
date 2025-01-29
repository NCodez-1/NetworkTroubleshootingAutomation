from netmiko import ConnectHandler
from datetime import datetime
import time
from colorama import Fore, Style

cisco_device = {
    'device_type': 'cisco_ios',
    'host': '192.168.0.100',
    'username': 'admin',
    'password': 'cisco',
    'port': 22,
    'secret': 'cisco'}


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


if __name__ == "__main__":
    while True:
        print(f"[{datetime.now}] Connected to {cisco_device['host']}")
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        check_interfaces()
        print(Fore.BLUE + "-" * 50 + Style.RESET_ALL)
        print(f"Waiting 10 seconds before next task")
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        time.sleep(10)
        show_vlan_brief()
        print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
        print(f"[{datetime.now()}] Connection closed")
        break
