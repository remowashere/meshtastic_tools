import meshtastic.serial_interface
from pubsub import pub
import time

# You can change the message and interval here
WARDRIVE_TEXT = "(autom. bericht) Hallo! Ik ben aan het rondrijden en op zoek naar nodes"
WARDRIVE_INTERVAL = 30

# Normally the Serialinterface will work fine if you use a USB connection
interface = meshtastic.serial_interface.SerialInterface()
#interface = meshtastic.StreamInterface()
#interface = /dev/bus/usb/002/002
#interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/bus/usb/002/002')


def find_new_nodes():
    """
    Wait for the specified number of seconds. Return
    True if a new node was added to the list. False
    otherwise.
    """
    start_count = len(interface.nodes)
    
    for _ in range(WARDRIVE_INTERVAL):
        time.sleep(1)
        if len(interface.nodes) > start_count:
            return True

    return False


def wardrive():
    while True:
        interface.sendText(WARDRIVE_TEXT)

        if find_new_nodes():
            print("Found a friend!")
            break
        else:
            print("No new nodes yet :-(")


if __name__ == "__main__":
    print("Meshtastic wardrive has started")
    wardrive()
