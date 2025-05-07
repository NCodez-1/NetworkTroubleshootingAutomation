from openai import api_key
from pyfiglet import Figlet
import CiscoFuncs
from CiscoFuncs import *
from datetime import datetime
import time
from colorama import Fore, Style

""" This is a protoype of a program which can remotley access network devices and run troublehshooting
    commands, it is currently just the set up for data collection adn example of what can be done,
    current feautres allows inputting network deivces in the topology so they can be remotley accesses
    logs a example of a interface check and allows viewing content of the log file. 

    for the next stages the log format to be sent to the ELK stack will need to be intergrated with this    
    to be able to create custom logs based on the outcome of the device commands.

    Once the network topology is set up this can be scritped to run in the back ground checking certain commands
    and returning errors to the visual dashboard and then further intergrated with playbooks that work to fix 
    issues if can be done remotley """

CiscoFuncs.load_api_key()
api_key = CiscoFuncs.get_api_key()

if api_key:
    print(Fore.GREEN + f"API Key is set to: ${api_key}")
else:
    print(Fore.RED + "API Key is not set.")

def mainMenu():

    while True:

        f = Figlet(font='slant')

        print(Fore.GREEN + f.renderText("COM 617") + Style.RESET_ALL)
        print("Cisco Industrial consultancy project for COM617")
        print("This project aims to automatically and remotely troubleshoot Cisco network devices")
        print("The goals for this program is to remotely access a chosen device, run troubleshooting commands and "
              "raise any errors detected and process these as logs which can be passed through the ELK stack "
              "for visualization")
        
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Main Menu")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Add a device                      [1]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " View devices                      [2]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Run automated scans               [3]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Select an interface to check      [4]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " View log file contents            [5]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " AI Menu                           [6]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Exit                             [99]")
        print(Fore.BLUE + "-" * 50)

        option = int(input(Fore.GREEN + " Choose an option: "))
        
        """ This option allows for each device in the network topology to be added to the program to allow remote access """
    
        if option == 1:
            while True:
                add_devices()
                another = input(Fore.GREEN + "Add another device? 'Y', 'N' ").strip().lower()

                if another == 'y':
                    continue
                elif another == 'n':
                    break
                else:
                    print(Fore.RED + "Invalid option. Please enter 'Y' or 'N'.")
                    
    # This gives an overview of all devices in the topology and the address they are at
    
        elif option == 2:
            list_devices()
            input(Fore.GREEN + "\nPress Enter to return to the menu...")
            continue
            
    # selects a device to SSH int and runs a set of automated commands
    
        elif option == 3:
            cisco_device = select_device()
            print(Fore.GREEN + "Running automated tasks")
            print(Fore.RED + "Press ctrl+ to stop" + Style.RESET_ALL)
            print(f"[{datetime.now}] Connected to {cisco_device['host']}")

            try:
                while True:
                    print(Fore.GREEN + "-" * 100 + Style.RESET_ALL)
                    check_interfaces(cisco_device)
                    print(Fore.GREEN + "-" * 100 + Style.RESET_ALL)
                    print(f"Waiting 5 seconds before next task")
                    print(Fore.GREEN + "-" * 100 + Style.RESET_ALL)
                    time.sleep(5)
                    show_vlan_brief(cisco_device)
                    print(Fore.GREEN + "-" * 100 + Style.RESET_ALL)
                    time.sleep(5)


            except KeyboardInterrupt:
                print(Fore.GREEN + "\nExiting tasks" + Style.RESET_ALL)
            continue
            
            """ This is an example function of being able to remotley access a device, check the status of it, here its interface status and then 
            returns the relevant information as a JSON log """
    
        elif option == 4:
            cisco_device = select_device()
            log_interface(cisco_device)
            continue
            
# Thsi just prints out a number of lines of the saved log file

        elif option == 5:
            lineCount = int(input("Choose number of lines to sample from file: " + Style.RESET_ALL))
            logs(lineCount)
            option = input(Fore.GREEN + "\nPress Enter to return to the menu...")

        elif option == 6:
            AImenu()

        elif option == 99:
            print(Fore.GREEN + f.renderText("Exiting"))
            quit()
        else:
            print("Choose an option")


def AImenu():
    while True:
        f = Figlet(font='slant')
        print(Fore.GREEN + f.renderText("COM 617") + Style.RESET_ALL)

        print("Cisco Industrial consultancy project for COM617")
        print("This project aims to automatically and remotely troubleshoot Cisco network devices")
        print("The goals for this program is to remotely access a chosen device, run troubleshooting commands and "
              "raise any errors detected and process these as logs which can be passed through the ELK stack "
              "for visualization")

        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " AI Menu")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Show API Key                       [1]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Change API Key                     [2]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Remove API Key                     [3]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Add rule with AI                   [4]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Back                               [99]")
        print(Fore.BLUE + "-" * 50)

        try:
            option = int(input(Fore.GREEN + " Choose an option: "))
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a valid number.")
            continue

        # Show API Key
        if option == 1:
            key = CiscoFuncs.get_api_key()
            if key:
                print(Fore.GREEN + f"API Key is set to: {key}")
            else:
                print(Fore.RED + "API Key is not set.")

        # Change API Key
        elif option == 2:
            while True:
                another = input(Fore.GREEN + "Need instructions to change the API Key? 'Y', 'N': ").strip().lower()
                if another == 'y':
                    print(Fore.GREEN + "1) Visit the following website and create an account:   " + Fore.YELLOW + "https://aimlapi.com")
                    print(Fore.GREEN + "2) When logged in navigate to the 'Key Management':     " + Fore.YELLOW + "https://aimlapi.com/app/keys")
                    print(Fore.GREEN + "3) Press on 'Create API Key' and give it an optional name.")
                    print(Fore.GREEN + "4) Then copy created key to the clipboard.")
                    print(Fore.GREEN + "5) Paste the copied key into the following prompt.")
                if another in ('y', 'n'):
                    new_key = input(Fore.GREEN + "Enter your new API key: ").strip()
                    CiscoFuncs.set_api_key(new_key)
                    print(Fore.GREEN + f"API key successfully set to: {CiscoFuncs.get_api_key()}")
                    break
                else:
                    print(Fore.RED + "Invalid option. Please enter 'Y' or 'N'.")

        # Remove API Key
        elif option == 3:
            while True:
                another = input(Fore.RED + "Sure you want to delete the API Key? 'Y', 'N': ").strip().lower()
                if another == 'y':
                    CiscoFuncs.set_api_key("")
                    print(Fore.YELLOW + "API key has been cleared.")
                    break
                if another == 'n':
                    print(Fore.YELLOW + "API key was NOT removed.")
                    break
                else:
                    print(Fore.RED + "Invalid option. Please enter 'Y' or 'N'.")

        # Add rule with AI
        elif option == 4:
            ai_prompt_rule()

        elif option == 99:
            break

        else:
            print(Fore.RED + "Choose a valid option from the menu.")

if __name__ == "__main__":
    mainMenu()