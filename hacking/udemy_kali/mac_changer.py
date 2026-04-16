#!/usr/bin/env python

# MODULES
import subprocess
import optparse

# Check ifconfig
subprocess.call("ifconfig", shell=True)

# Parser Object, an instance of the OptionParser Class from optparse module
# object = module.Class
parser = optparse.OptionParser()
parser.add_option("-i", "--interface", dest="interface", help="Interface which will have new MAC address")
parser.add_option("-m", "--mac", dest="new_mac", help="New MAC address")

(options, arguments) = parser.parse_args()
interface = options.interface
new_mac = options.new_mac

# User Input Prompts
# interface = raw_input("Interface to change? ")
# new_mac = raw_input("New MAC address? ")

print("[+] Changing MAC address for " + interface + " to " + new_mac)

# subprocess.call("ifconfig eth0 down", shell=True)
# subprocess.call("ifconfig eth0 hw ether 00:11:22:33:44:66", shell=True)
# subprocess.call("ifconfig eth0 up", shell=True)

# subprocess.call("ifconfig " + interface + " down", shell=True)
# subprocess.call("ifconfig " + interface + " hw ether " + new_mac, shell=True)
# subprocess.call("ifconfig " + interface + " up", shell=True)
# subprocess.call("ifconfig " + interface, shell=True)

subprocess.call(["ifconfig", interface, "down"])
subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
subprocess.call(["ifconfig", interface, "up"])
subprocess.call(["ifconfig", interface])