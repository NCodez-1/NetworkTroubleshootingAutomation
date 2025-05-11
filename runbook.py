import json
from netmiko import BaseConnection, ConnectHandler, NetmikoTimeoutException
import re
from requests_toolbelt import MultipartEncoder
import requests

ROOMID = "Y2lzY29zcGFyazovL3VybjpURUFNOmV1LWNlbnRyYWwtMV9rL1JPT00vZTBjYzlmMzAtZWRmZC0xMWVmLThhMDQtMDVhN2ZkMjgxODQ5"
TOKEN = "Bearer MTY3MDhmYTMtOWUyYS00MzJmLTkwZDAtYTFjZTFkMzUwM2MzNjdmNjE1ZTEtYzBk_PE93_bde28e3d-21ec-426e-b7f1-1c7280ca363f"
DEVICES = "devices.json"

##TESTING
def log_to_console(log):
    print("[TEST ACTION] log_to_console triggered")
    print(log)

##TESTING END

#handle json files
def json_load(file: str) -> list:
    with open(file, 'r') as f:
        return json.load(f)

#create connection to a specified device based on the IP address
def netmiko_connection(ip_address: str) -> BaseConnection:
    ssh_connection = None
    try:
        ssh_connection = ConnectHandler(
            device_type = "cisco_ios",
            host = ip_address,
            username = "cisco",
            password = "cisco123!",
            port = 22
        )
    except NetmikoTimeoutException:
        print("Could not connect to ip address: %s" % ip_address)
    return ssh_connection

#retrieve interface from the log message
def get_interface(log: dict) -> str:
    x = re.findall("Interface.+[1-24]", log["message"])
    if x:
        return ''.join(x).strip().lower()
    else:
        return None    

#send message to cisco webex
def send_message(message: str, receiver: str, authorization: str) -> dict:
    url = "https://webexapis.com/v1/messages"
    payload = MultipartEncoder({
            "roomId": receiver,
            "text": message})
    headers = {
        'Authorization': authorization,
        'Content-Type': payload.content_type
        }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text

#retrieve IP address based on the mac address from the log 
def mac_to_ip(log: dict) -> str:
    x = log["message"].split(' ')[-1]
    #opens a file which contains hostname to IP address mappings
    mac = x[x.index(':')+1:]
    content = json_load(DEVICES)
    for i in content:
        if mac in i.values():
            return (i['ip'], mac)
    return None

def load_topology() -> dict:
    content = json_load(DEVICES)
    dic = {}

    for device in content:
        dic[device] = content[device]["ip"]

    return dic

def detect_ntp_issues(log: dict) -> bool:
    log_message = ["Authentication failed", "stratum too high", "time offset unacceptable", "unreachable"]
    for message in log_message:
        if message in log["message"]:
            return True
    return False

def shut_int(log: dict):
    ip_address = log["ip_address"]
    interface = get_interface(log)
    #creating connection to a device
    ssh_connection = netmiko_connection(ip_address)
    ssh_connection.enable()
    #sending set of commands to shutdown a specific interface 
    ssh_connection.send_config_set(["{}".format(interface), "shutdown"])
    #exiting config mode
    ssh_connection.exit_config_mode()
    #using show ip int brief, check whether the specified interfece actually went down
    check_status = ssh_connection.send_command('show ip int brief | include {}'.format(interface))
    if "down" not in check_status: 
        #in case the interface didnt go down send message to cisco webex
        error_message = "Could not turn down {0} on a device {1}".format(interface, ip_address)
        send_message(error_message, ROOMID, TOKEN)
    else:
        print('Shuting down "%s".' % (interface))
    ssh_connection.disconnect()

def up_int(log: dict):
    ip_address = log["ip_address"]
    interface = get_interface(log)
    #creating connection to a device
    ssh_connection = netmiko_connection(ip_address)
    ssh_connection.enable()
    #sending set of commands to put up a specific interface
    ssh_connection.send_config_set(["{}".format(interface), "no shutdown"])
    #exiting config mode
    ssh_connection.exit_config_mode()
    #using show ip int brief, check whether the specified interfece actually is up
    check_status = ssh_connection.send_command('show ip int brief | include {}'.format(interface))
    if "up" not in check_status: 
        #in case the interface isn't up send message to cisco webex
        error_message = "Could not turn up {0} on a device {1}".format(interface, ip_address)
        send_message(error_message, ROOMID, TOKEN)
    else:
        print('Turning up  "%s".' % (interface))
    ssh_connection.disconnect()

def STP_config(log):
    ip = mac_to_ip(log)
    #if mac address wasn't in the topology
    if not ip:
        #create hostname to IP mapping
        switches = load_topology()
        #get the IP address of S1
        curr_ip_address = switches['Switch1']
        hostname = "Switch1"
        while True:
            ssh_connection = netmiko_connection(curr_ip_address)
            stp_info = ssh_connection.send_command("show spanning-tree")
            #splitting the output of the "show sp" command by newline
            sp_output = stp_info.split('\n')
            #retrie cost
            cost = sp_output[4].strip().split()[1]
            #retrieve forwarding port to the root switch
            port = sp_output[5].strip().split()[1]
            next_interface = "Fas0/"+port[0:port.index('(')]
            next_interface1 = "Fa0/"+port[0:port.index('(')]
            #based on the STP cost if cost is equal to the values in the set that means this switch is connected to the root switch
            if int(cost) in {2,4,19,100}:
                ssh_connection.enable()
                #enabling root guard to the rouge switch
                ssh_connection.send_config_set(["interface {}".format(next_interface1), "spanning-tree guard root"])
                #sending message to cisco webex
                message = "Blocked the rouge switch connected to {0} on interface {1}".format(hostname, next_interface1)
                send_message(message, ROOMID, TOKEN)
                break
            #if cost is different than the set
            else:
                neighbors = ssh_connection.send_command("show cdp neighbors")
                #splitting the result and retrieving info about the neighbours
                neighbor_interfaces = neighbors.split('\n')[3:]
                for i in neighbor_interfaces:
                    #retrieving only local interfaces of the neighbours
                    int1= ''.join(i.split()[1:3])
                    #if the neigbour interface is the same as the one that leads to the root 
                    if int1 == next_interface:
                        #returns the hostname of the switch it needs to connect next
                        hostname = i.split()[0]
                        curr_ip_address = switches[hostname]
    else:
        content = json_load(DEVICES)
        #create a list of the IP adressess and bridge priority of the switches
        switches = [(content[device]['ip'], content[device]['bridge_priority']) for device in content if "Switch" in device]
        for device in switches:
        #creating connection to my VM router in the final version it will look: ssh_connection = netmiko_connection(ip_address)
            ssh_connection = netmiko_connection(device[0])
            stp_info = ssh_connection.send_command("show spanning-tree")
            n_bridge = re.search("Bridge.+(\d)").split()[3]
            if n_bridge != device[1]:
                ssh_connection.send_config_set(["spanning-tree vlan 1 priority {0}".format(device[1])])
                message = "Set STP priority back to {0} on {1}".format(device[1], device[0])
                send_message(message, ROOMID, TOKEN)
    ssh_connection.disconnect()

def NTP(log: dict):
    if detect_ntp_issues(log["message"]):
        content = json_load(DEVICES)
        ntp_server = next((content[device]["ip"] for device in content if device == "Router1"), None)

        ssh_connection = netmiko_connection(log["ip_address"])
        if log["ip_address"] == ntp_server:
            ssh_connection.enable()
            ssh_connection.send_command("ntp master 3")
            ssh_connection.exit_config_mode()
            check = ssh_connection.send_command("show ntp status | include ntp")
            if "master 3" in check:
                message = "Router1 is set to NTP master"
                send_message(message, ROOMID, TOKEN)
            else:
                message = "Could not set NTP master on Router1"
                send_message(message, ROOMID, TOKEN)
        else:
            ssh_connection.enable()
            untrusted_server = re.findall("(?:[0-9]{1,3}\.){3}[0-9]{1,3}", log["message"])
            ssh_connection.send_config_set(['no ntp server {}'.format(untrusted_server[0]), 'ntp server {}'.format(ntp_server)])
            check = ssh_connection.send_command("show ntp status | include ntp")
            if ntp_server in check:
                message = "NTP server is set to {}".format(ntp_server)
                send_message(message, ROOMID, TOKEN)
            else:
                message = "Problem with setting a NTP server on {} device".format(log["ip_address"])
                send_message(message, ROOMID, TOKEN)

    ssh_connection.disconnect()


events_and_actions = {
    'state to up' : shut_int,
    'state to down': up_int,
    'Root bridge' : STP_config,
    'Authentication failed' : NTP,
    'stratum too high' : NTP,
    'time offset unacceptable' : NTP,
    'unreachable' : NTP,
    'testing' : log_to_console
}