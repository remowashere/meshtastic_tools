import meshtastic.serial_interface
from pubsub import pub
import time
import requests
from bs4 import BeautifulSoup
import re
import textwrap

#
# This will make your node a standalone offline 'Wikipedia' source
# As soon as it's receives a message, it will look up the searchterm and return the first paragraph of the Wikipedia entry
# 
# You will need:
# - a locally hosted Kiwix (e.g. docker) installation with the 'wikipedia_nl_all' offline catalog
#
# You have to:
# - change the url in the script so it matches your local IP of the Kiwix installation
#

# Default reply on a ping
PING_TEXT = "Received your ping, here's my PONG!"

# Normally the Serialinterface will work fine if you use a USB connection
interface = meshtastic.serial_interface.SerialInterface()

def onReceive(packet, interface):  # called when a packet arrives

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

            #print(f"Bericht ontvangen: {packet}")

            # the keyword is 'ping', in that case send reply
            if 'ping' in str(decoded.get('payload').lower()):
                interface.sendText(PING_TEXT, packet.get('from'))

            received_text = decoded.get('payload').lower()

            print("We got a Wiki search: ", str(received_text))

            # Search our Wiki
            text = getSearchResult(received_text.title())
            print("This is what I found: ", text)

            if not text:
                interface.sendText("Sorry, deze zoekterm is niet gevonden", packet.get('from'))
                return

            #html = header.html
            #text = header.get_text()

            #response = "\n ".join(textwrap.wrap(text, width=200, break_long_words=False))
            response = textwrap.wrap(text, width=200, break_long_words=False)

            for text in response:
                print("Sending text: ", text)
                time.sleep(5)
                interface.sendText(text, packet.get('from'))

            return

            # limit the text to 200 characters
            text = (text[:200] + '..') if len(text) > 200 else text

            # return the first paragraph
            interface.sendText(text, packet.get('from'))

            return

def wiki_request(full_url):
    try:
        html_content = requests.get(full_url, timeout=10)
        html_content.encoding = html_content.apparent_encoding
        html_content.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error")
        print(errh.args[0])
        return False
    return html_content


def cleanHTML(html):
    return re.sub(r'\n\s*\n', r'\n\n', html.strip(), flags=re.M)

def getSearchResult(searchterm, searching=True):

    print(" - searching for: ", searchterm)
    url = "http://10.20.0.2:8181/content/wikipedia_nl_all/A/"
    url_as_b = str.encode(url)
    full_url = url_as_b + searchterm
    full_url = full_url.decode("utf-8")
    full_url = full_url.replace(" ", "_")
    print(" - checking URL: ", full_url)
    html_content = wiki_request(full_url)

    # doorverwijspagina?
    if html_content:
        soup = BeautifulSoup(html_content.text, 'html.parser')
        if soup.body.findAll(string='doorverwijspagina'):
            print("   - oh oh, this is a redirect page")
            mf_section = soup.find('div', {'class': 'mf-section-0'})
            first_paragraph = mf_section.find('a')
            text = first_paragraph.get_text()
            text = cleanHTML(text)
            print("   - this is the first link I found: {}".format(text))
            return getSearchResult(text.encode(), searching=False)

    # if no page is found, try to search for the term
    if not html_content:

        if searching is False:
            return False

        url = "http://10.20.0.2:8181/search?content=wikipedia_nl_all&pattern="
        url_as_b = str.encode(url)
        full_url = url_as_b + searchterm.title()
        full_url = full_url.decode("utf-8")
        full_url = full_url.replace(" ", "%20")

        # perform a search
        print(" - Hmm, that didn't return anything, performing a global search")
        search_results = wiki_request(full_url)
        if search_results is False:
            return False

        # Search results can be empty
        soup = BeautifulSoup(search_results.text, 'html.parser')
        mf_section = soup.find('div', {'class': 'results'})
        first_paragraph = mf_section.find('a')

        if not first_paragraph:
            print("   - No search results found :(")
            return False

        # We have a search result
        text = first_paragraph.get_text()
        text = cleanHTML(text)
        #print("   - Full text for search result: ", text)
        print("   - Full paragraph: ", first_paragraph)
        return getSearchResult(text.encode(), searching=False)

        # perform a new request with the first result
        html_content = getSearchResult(text.encode(), searching=False)
        if html_content is False:
            return False

    print(" - Returning the first paragraph")
    print(html_content)

    soup = BeautifulSoup(html_content.text, 'html.parser')
    mf_section = soup.find('div', {'class': 'mf-section-0'})
    first_paragraph = mf_section.find('p')
    text = first_paragraph.get_text()
    text = cleanHTML(text)

    return text


if __name__ == "__main__":
    pub.subscribe(onReceive, "meshtastic.receive")
    while True:
        time.sleep(1000)
