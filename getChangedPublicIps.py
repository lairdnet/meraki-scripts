import requests
import json
import os
import argparse

#https://developer.cisco.com/meraki/api-latest/

API_KEY = str(os.environ.get("MERAKI_API_KEY"))
ORG_ID = str(os.environ.get("MERAKI_ORG_ID"))
DEBUG = False

def getOrganizations():

    url = "https://api.meraki.com/api/v1/organizations"

    payload = None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": API_KEY
    }

    response = requests.request('GET', url, headers=headers, data = payload)
    orgs = json.loads(response.text)
    return orgs


def getNetworkName(networkId):

    url = "https://api.meraki.com/api/v1/networks/" + networkId

    payload = None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": API_KEY
    }

    response = requests.request('GET', url, headers=headers, data = payload)
    network = json.loads(response.text)
    return network["name"]

def getPublicIps():

    url = "https://api.meraki.com/api/v1/organizations/" + ORG_ID + "/uplinks/statuses"

    payload = None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": API_KEY
    }

    response = requests.request('GET', url, headers=headers, data = payload)

    networkUplinks = json.loads(response.text)

    networks = []

    for index, networkUplink in enumerate(networkUplinks):
        
        networkName = getNetworkName(networkUplink["networkId"])
        #print(getNetworkName(networkUplink["networkId"]))
        networks.append({"networkName":networkName,"uplinks":[]})

        for uplink in networkUplink["uplinks"]:
            #print(uplink["interface"] + ":" + uplink["publicIp"])
            networks[index]["uplinks"].append({uplink["interface"]:uplink["publicIp"]})
        
    return json.dumps(networks, indent=4)

def getChangedPublicIps(currentPublicIps):

    #read in last public ips get
    if os.path.exists("current_ips.json"):
        lastIPsFile = open('current_ips.json')
    else:
        lastIPsFile = open('current_ips.json.template')
    lastPublicIps = json.load(lastIPsFile)

    #write out last ips
    if not DEBUG:
        with open("last_ips.json", "w") as lastFile:
            json.dump(lastPublicIps, lastFile, indent=4)

    #write out current ips
    with open("current_ips.json", "w") as currentFile:
        currentFile.write(currentPublicIps)

    with open("last_ips.json", "r") as f1:
        file1 = json.loads(f1.read())
    
    with open("current_ips.json", "r") as f2:
        file2 = json.loads(f2.read())

    message = "\nMERAKI WAN IP CHANGES\n\n"
    print (message)
    message = ""

    for item in file2:
        if item not in file1:
            found = False
            for entry in file1:
                if item["networkName"] == entry["networkName"]:
                    message += "CHANGED : " + item["networkName"] + "\n"
                    message += "\tPrevious: " + str(entry) + "\n"
                    message += "\tCurrent: " + str(item) + "\n\n"
                    found = True
                    break;

            if not found:
                message += "NEW : Network Detected: " + str(item) + "\n\n"
                
   

    if message == "":
        print("No changes detected.\n\n")
    else:
        print(message + "\n\n")

def checkReqs():
    
    if API_KEY is None and os.environ.get("MERAKI_API_KEY") is None:
        raise Exception("Missing required environment variable MERAKI_API_KEY")

    if ORG_ID is None and os.environ.get("MERAKI_ORG_ID") is None:
        raise Exception("Missing required environment variable MERAKI_ORG_ID")

def main():

    checkReqs()

    #get current wan public ips
    currentPublicIps = getPublicIps()

    #get changed ips from last run
    getChangedPublicIps(currentPublicIps)

    #display
    if DEBUG:
        print(getOrganizations())
        print(currentPublicIps)

#get args
#https://docs.python.org/3/library/argparse.html
parser = argparse.ArgumentParser(description="""
This script will check for changes in Meraki WAN IP addresses. 
""")
parser.add_argument("--api-key", help="Meraki API Key")
parser.add_argument("--org-id", help="Meraki Organization ID")
parser.add_argument("--debug", action=argparse.BooleanOptionalAction, help="Debug mode for additional output, True/False", default=False, type=bool)

args = parser.parse_args()

if args.api_key:
    API_KEY = args.api_key
if args.org_id:
    ORG_ID = args.org_id
# if args.debug:
DEBUG = args.debug

#run main
main()