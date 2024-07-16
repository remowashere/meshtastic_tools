import meshtastic.serial_interface
from pubsub import pub
import time

# You can change the message and interval here
PING_TEXT = "Received your ping, here's my PONG!"

# Normally the Serialinterface will work fine if you use a USB connection
interface = meshtastic.serial_interface.SerialInterface()
#interface = meshtastic.StreamInterface()
#interface = /dev/bus/usb/002/002
#interface = meshtastic.serial_interface.SerialInterface(devPath='/dev/bus/usb/002/002')


def onReceive(packet, interface): # called when a packet arrives

    """
    {
        'from': 420101xxxx, 
        'to': 208629xxxx, 
        'decoded': {
            'portnum': 'TEXT_MESSAGE_APP',
            'payload': b'test', 
            'text': 'test'
        }, 
        'id': 1352182408, 
        'rxSnr': 6.5, 
        'hopLimit': 3, 
        'wantAck': True, 
        'rxRssi': -15, 
        'hopStart': 3, 
        
        'raw': from: 420101xxxx
        to: 20862xxxx
        decoded {
            portnum: TEXT_MESSAGE_APP
            payload: "test"
        }
        id: 1352182408
        rx_snr: 6.5
        hop_limit: 3
        want_ack: true
        rx_rssi: -15
        hop_start: 3
        , 
        'fromId': '!fa66xxxx', 
        'toId': '!7c5axxxx'
    }
    """

    if packet.get('decoded'):
        decoded = packet.get('decoded')
        
        # we only want to check real text messages and no telemetry and other stuff
        if decoded.get('portnum') == "TEXT_MESSAGE_APP":
            print(f"Bericht ontvangen: {packet}")

            # the keyword is 'ping', in that case send reply
            if 'ping' in str(decoded.get('payload').lower()):
                interface.sendText(PING_TEXT, packet.get('from'))


if __name__ == "__main__":
    pub.subscribe(onReceive, "meshtastic.receive")
    while True:
        time.sleep(1000)
