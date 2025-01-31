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
        print(Fore.GREEN + " Run automated scans               [1]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Select an interface to check      [2]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " View log file contents            [3]")
        print(Fore.BLUE + "-" * 50)
        print(Fore.GREEN + " Exit                              [4]")
        print(Fore.BLUE + "-" * 50)

        option = int(input(Fore.GREEN + " Choose an option: "))
        if option == 1:
            print(Fore.GREEN + "Running automated tasks")
            print(f"[{datetime.now}] Connected to {cisco_device['host']}")

            try:
                while True:
                    print(Fore.GREEN + "-" * 100 + Style.RESET_ALL)
                    check_interfaces()
                    print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
                    print(f"Waiting 5 seconds before next task")
                    print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
                    time.sleep(5)
                    show_vlan_brief()
                    print(Fore.BLUE + "-" * 100 + Style.RESET_ALL)
                    time.sleep(5)
                    """ 
                    This function would normally have a Ctrl+C to stop the running tasks but since that doesnt work in Pycharms terminal
                    Ive added in a type exit to stop instead, In the final program this will be removed
                    """
                    user_input = input("Type 'exit' to stop: ").strip().lower()
                    if user_input == "exit":
                        print(Fore.RED + "Exiting automated tasks..." + Style.RESET_ALL)
                        break

            except KeyboardInterrupt:
                print(Fore.GREEN + "\nExiting tasks" + Style.RESET_ALL)
            mainMenu()

        elif option == 2:
            log_interface()
            mainMenu()

        elif option == 3:
            lineCount = int(input("Choose number of lines to sample from file: " + Style.RESET_ALL))
            Logs(lineCount)
            option = input("Return to main or exit (M or E): ")
            if option == ('m' or 'M'):
                mainMenu()
            else:
                option == ('e' or 'E')
                print(Fore.GREEN + f.renderText("Exiting"))
                quit()

        elif option == 4:
            print(Fore.GREEN + f.renderText("Exiting"))
            quit()
        else:
            print("Choose an option")


if __name__ == "__main__":
    mainMenu()

