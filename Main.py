from pyfiglet import Figlet
from CiscoFuncs import *
from datetime import datetime
import time
from colorama import Fore, Style


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
        print(Fore.GREEN + " Exit                              [6]")
        print(Fore.BLUE + "-" * 50)

        option = int(input(Fore.GREEN + " Choose an option: "))

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

        elif option == 2:
            list_devices()
            input(Fore.GREEN + "\nPress Enter to return to the menu...")
            continue

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

       elif option == 4:
            cisco_device = select_device()
            log_interface(cisco_device)
            continue

        elif option == 5:
            lineCount = int(input("Choose number of lines to sample from file: " + Style.RESET_ALL))
            logs(lineCount)
            option = input(Fore.GREEN + "\nPress Enter to return to the menu...")

        elif option == 6:
            print(Fore.GREEN + f.renderText("Exiting"))
            quit()
        else:
            print("Choose an option")


if __name__ == "__main__":
    mainMenu()


