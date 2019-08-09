#!/usr/bin/env python
'''
Make sure to set the DHCP timeout in /etc/dhcp/dhclient.conf to a lower value. 5 seems to work well.

TODO: Allow a specific channel. iw seems to default to all after four channels though. Bug?
'''

import subprocess
import os
import time
import argparse
import random
import logging
import netifaces as ni
from datetime import datetime, timedelta

# EDIT THESE VARIABLS
# SCORE_URL = 'http://172.16.100.1/cgi-bin/score.php?team_name=Majestic12'
SCORE_URL = 'http://{}/cgi-bin/score.php?team_name=blah'
TRUE_FACE = '0x9ed' # 0x21 RPI 0x9ed ZC 0x0c blunder

# DO NOT EDIT THESE VARIABLES
TWOG_CHANS = '2412 2417 2422 2427 2432 2437 2442 2447 2452 2457 2462'
# FIVEG_CHANS = '5180 5200 5220 5240 5260 5280 5300 5500 5520 5540 5560 5580 5660 5680 5700 5745 5765 5785 5805 5825'
FIVEG_CHANS = '5180 5200 5220 5240 5745 5765 5785 5805 5825'
FORMAT = '[%(levelname)s %(asctime)-15s] --- %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def slay_king(interface, ssid, ip, scan_freq):
    # Make sure the interface is not connected before going into the loop
    os.system(f'ip link set {interface} down')
    os.system(f'ip link set {interface} up')
    os.system(f'iw {interface} disconnect')
    reset_time_elapsed = False

    while True:
        proc = subprocess.Popen(f'iw dev {interface} scan freq {scan_freq} 2>/dev/null | grep -A35 -B8 {ssid} | egrep "BSS [a-f0-9][a-f0-9]|SSID: |freq: |Capabilities: 0x"', shell=True, stdout=subprocess.PIPE)
        stdout_str = proc.communicate()[0].decode('utf-8')
#        print(stdout_str)
        stdout_list = stdout_str.split('\n')

        # BSS e4:f4:c6:08:2b:97(on wlan0)
        # freq: 2427
        # Capabilities: 0x9ad

        for line in stdout_list:
            line = line.strip()

            if 'BSS' in line:
                bssid = line[4:21]
                freq = ''
                continue
            
            if 'freq' in line:
                freq = line.split(' ')[1]
                continue
            
            if 'SSID' in line:
                try:
                    essid = line.split(' ')[1]
                except:
                    essid = ''
                continue

            if 'Capabilities' in line:
                if line.split(' ')[1] != '' and bssid != '' and essid == ssid:
                    print(line.split(' ')[1])
                    # Connect to the good access point by ssid, bssid, and frequency
                    logging.info('CONNECT STAGE')
                    logging.debug(f'iw {interface} connect -w {ssid} {freq} {bssid}')
                    os.system(f'iw {interface} connect -w {ssid} {freq} {bssid}')

                    # If no static IP given perform DHCP.
                    if ip is None:
                        logging.info('DHCP STAGE')
                        os.system(f'ip addr flush dev {interface}')
                        os.system(f'dhclient {interface}')
                        try:
                            interface_ip = ni.ifaddresses(str(f'{interface}'))[ni.AF_INET][0]['addr']
                        except:
                            # hot fix for when DHCP fails
                            interface_ip = '172.16.100.112'
                        logging.info(f'DHCP Address: {interface_ip}')
                        octets = interface_ip.split('.')
                        octets[3] = '1'
                        gateway_ip = '.'.join(octets)
                        logging.info(f'Gateway Address: {gateway_ip}')
                        # url = SCORE_URL
                        url = SCORE_URL.format(gateway_ip)
                    else:
                        # url = SCORE_URL
                        url = SCORE_URL.format(ip)

                    # Attempt to score using wget with max tries of 4. Typically scores on the second try for whatever reason... server likely still coming up.
                    logging.info('WGET STAGE')         
                    os.system(f'wget -i {interface} -T 4 --user-agent="MJ12" --tries=4 {url}')

                    # Notify user
                    logging.info(f'Attempted to score on BSSID: {bssid}  --  Channel: {freq}. Sleeping 5 seconds and reseting...\n\n')

                    # Reset everything. Sleep for 10 seconds gives enough time for server to go down before we start scanning again.
                    os.system(f'iw {interface} disconnect')
                    os.system(f'ip link set {interface} down')
                    os.system(f'ip link set {interface} up')
                    bssid = ''
                    essid = ''
                    freq = ''
                    time.sleep(5)
                    break

        time.sleep(.35)
        logging.info(f'Scanning for New Hill with {interface}')

def main():
    parser = argparse.ArgumentParser(description='MFG - A hill may wear many faces, but the Many Face God sees through them all.')
    parser.add_argument('-i', '--interface', default='wlan0', help='Network interface to launch attack from.')
    parser.add_argument('-c', '--channel', default='all', choices=['2.4','5','all'], help='Channels to scan for SSID.')
    parser.add_argument('-t', '--target', default='WCTF_KingOfTheHill', help='Target SSID to filter for when scanning.')
    parser.add_argument('--static', default=None, help='Use a static IP for the gateway. This will also set a static IP on the interface within the /24 subnet.')

    args = parser.parse_args()
    
    # Parse and set the channel option.
    if args.channel == '2.4':
        channels = TWOG_CHANS
    elif args.channel == '5':
        channels = FIVEG_CHANS
    else:
        channels = TWOG_CHANS + ' ' + FIVEG_CHANS

    # Set a static IP on the interface.
    if args.static is not None:
        logging.info('Setting Static IP')
        octets = args.static.split('.')
        octets[3] = str(random.randint(100,120))
        interface_ip = '.'.join(octets)
        logging.info('Clearing any previous static IPs on interface.')
        os.system(f'ip addr flush dev {args.interface}')
        logging.info(f'Setting the IP for {args.interface} to {interface_ip}.')
        os.system(f'ip addr add {interface_ip}/24 dev {args.interface}')

    # Start scanning with the set options.
    slay_king(args.interface, args.target, args.static, channels)

if __name__ == "__main__":
    main()
