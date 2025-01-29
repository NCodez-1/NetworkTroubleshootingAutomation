from netmiko import ConnectHandler
from datetime import datetime

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
        print(f"[{datetime.now}] Connected to {cisco_device['host']}")

        if 'secret' in cisco_device:
            connection.enable()

        output = connection.send_command("show ip interface brief")
        print(f"interface Status\n{output}")
        connection.disconnect()
        print(f"[{datetime.now()}] Connection closed")

    except Exception as e:
        print(f"Error {e}")


if __name__ == "__main__":
    check_interfaces()
