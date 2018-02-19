
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# This is for json and request connections


bigip1_address = '{{ b1_addr }}'
bigip1_name = '{{ b1_name }}'
bigip2_address = '{{ b2_addr }}'
bigip2_name = '{{ b2_name }}'
bigip_user = '{{ user  }}'
bigip_pass = '{{ pass }}'
ha_vlan_name = '{{ ha_vname }}'
ha_interface = '{{ ha_intf }}'
ha_self_name = '{{ ha_self }}'


# Create two BIG-IP dictionaries and then make a list of them for iterating through setup


bigip1 = {
    "node" : 1,
    "address" : bigip1_address,
    "name": bigip1_name,
    "user" : bigip_user,
    "pass" : bigip_pass,
    "ha_self_ip" : "{{ b1_ha_selfip }}",
    "ha_vlan_name" : ha_vlan_name,
    "ha_interface" : ha_interface,
    "ha_self_name" : ha_self_name,
    "configsyncIp" : "{{ b1_syncip }}",
    "peerIp": bigip2_address,
    "peerName": bigip2_name
}

bigip2 = {
    "node" : 2,
    "address" : bigip2_address,
    "name": bigip2_name,
    "user" : bigip_user,
    "pass" : bigip_pass,
    "ha_self_ip" : "{{ b2_ha_selfip }}",
    "ha_vlan_name" : ha_vlan_name,
    "ha_interface" : ha_interface,
    "ha_self_name" : ha_self_name,
    "configsyncIp" : "{{ b2_syncip }}",
    "peerIp": bigip1_address,
    "peerName": bigip1_name
}

bigips = [bigip1,bigip2]


# Create a floating IP list of objects, if more VLANs exists, add floats to this list


float = []
float.append({"name":"Internal-Float","address":"{{ float_internal }}","vlan":"internal"})
float.append({"name":"DMZ-Float","address":"{{ float_dmz }}","vlan":"dmz"})


# Check to see if AAA is using direct or Pool method, stop if direct


def get_radius_list(bigip,bigips):
    address = bigips["address"]
    response = bigip.get("https://" + address + "/mgmt/tm/apm/aaa/radius")
    rad_server_list = (json.loads(response.text)["items"])
    return rad_server_list

def radius_check(bigip,bigips):
    count = 0
    for x in get_radius_list(bigip,bigips):
        print ("  " + x["name"] + " has use pool " + x["usePool"])
        if x["usePool"] == "disabled":
            count = count + 1
    return count

def resp_func(resp):
    resp_text = json.loads(resp.text)
    code = str(resp.status_code)
    if code != "200":
        print ("    HTTP Error " + str(resp.status_code) + ": " + resp_text["message"])
    elif code == "200":
        print ("    HTTP OK: " + " " + resp_text["name"] + " has been created")
    else:
        print ('    Sorry something went wrong')


# PHASE 1 FUNCTIONS: THESE ARE RUN FOR EACH BIGIP
# TO SETUP VLANS, SELF-IP AND FLOATING IPS


def create_ha_vlan(bigips):
    print ("  Creating HA VLAN")
    payload = {}
    payload['name'] = bigips["ha_vlan_name"]
    payload['interfaces'] = [{"name":bigips["ha_interface"],"tagged":False}]
    address = bigips["address"]
    resp = bigip.post("https://" + address + "/mgmt/tm/net/vlan",data=json.dumps(payload))
    resp_func(resp)

def create_ha_self(bigips):
    print ("  Creating HA Self IP")
    payload = {}
    payload['name'] = bigips["ha_self_name"]
    payload['address'] = bigips["ha_self_ip"]
    payload['vlan'] = bigips["ha_vlan_name"]
    payload['allow-service'] = ["default"]
    address = bigips["address"]
    resp = bigip.post("https://" + address + "/mgmt/tm/net/self",data=json.dumps(payload))
    resp_func(resp)

def create_floats(bigips):
    print ("  Creating Floating IPs")
    for float_payload in float:
        float_payload['allow-service'] = ["default"]
        float_payload['floating'] = "enabled"
        float_payload['trafficGroup'] = "traffic-group-1"
        address = bigips["address"]
        resp = bigip.post("https://" + address + "/mgmt/tm/net/self",data=json.dumps(float_payload))
        resp_func(resp)


# Configure ConfigSync, Mirroring and Failover parameters


def config_sync(bigips):
    print ("Configuring sync parameters")
    payload = {}
    syncIp = bigips["configsyncIp"]
    payload["configsyncIp"] = syncIp
    payload["mirrorIp"] = syncIp
    payload["mirrorSecondaryIp"] = "any6"
    payload["unicastAddress"] = [{"effectiveIp": syncIp,"effectivePort":1026,"ip": syncIp,"port":1026}]
    address = bigips["address"]
    name = bigips["name"]
    resp = bigip.patch("https://" + address + "/mgmt/tm/cm/device/~Common~" + name,data=json.dumps(payload))
    resp_text = json.loads(resp.text)
    code = str(resp.status_code)
    if code != "200":
        print ("    HTTP Error " + str(resp.status_code) + ": " + resp_text["message"])
    elif code == "200":
        print ("    HTTP OK: " + "ConfigSync parameters have been configured")
    else:
        print ('    Sorry something went wrong')


# PHASE 1 LOOP: THIS RUNS THE FUNCTIONS ABOVE FOR EACH BIG-IP


def setup_ha_bigip(bigip,bigips,float):
    create_ha_vlan(bigips)
    create_ha_self(bigips)
    create_floats(bigips)
    config_sync(bigips)


# PHASE 2 FUNCTIONS: THESE ARE CALLED FOR BIGIP-1 ONLY


def create_trust(bigip,bigips):
    print ("Creating HA pair now...")
    payload = {}
    payload["command"] = "run"
    payload["name"] = "root"
    payload["caDevice"] = True
    payload["device"] = bigips["peerIp"]
    payload["deviceName"] = bigips["peerName"]
    payload["username"] = bigips["user"]
    payload["password"] = bigips["pass"]
    address = bigips["address"]
    #print (payload)
    post = bigip.post("https://" + address + "/mgmt/tm/cm/add-to-trust",data=json.dumps(payload))
    print (post.text)

def init_sync(bigip,bigips):
    payload = {}
    payload["command"] = "run"
    payload["options"] = [{"to-group":"device_trust_group","force-full-load-push": True}]
    address = bigips["address"]
    post = bigip.post("https://" + address + "/mgmt/tm/cm/config-sync",data=json.dumps(payload))
    print (post.text)

def create_dev_group(bigip,bigips):
    print ("Creating Device Group...")
    payload = {}
    payload["name"] = "DeviceGroup1"
    payload["type"] = "sync-failover"
    payload["autoSync"] = "disabled"
    payload["devices"] = [bigip1_name, bigip2_name]
    address = bigips["address"]
    post = bigip.post("https://" + address + "/mgmt/tm/cm/device-group",data=json.dumps(payload))
    print (post.text)

def init_sync_dg1(bigip,bigips):
    print ("Performing initial sync...")
    payload = {}
    payload["command"] = "run"
    payload["options"] = [{"to-group":"DeviceGroup1"}]
    address = bigips["address"]
    post = bigip.post("https://" + address + "/mgmt/tm/cm/config-sync",data=json.dumps(payload))
    print (post.text)


# Main iteration loop to cycle thorugh the list if BIG-IPs


for node in bigips:
    print ("Working on F5 number " + str(node["node"]))
    bigip = requests.session()
    bigip.auth = (node["user"],node["pass"])
    bigip.verify = False
    bigip.headers.update({'Content-Type' : 'application/json'})
    if node["node"] == 2:
        # continue
        # node2 preconfig
        setup_ha_bigip(bigip,node,float)
    elif node["node"] == 1:
        if radius_check(bigip,node) > 0:
            print ("  Please configure Radius servers to use Pools before continuing with HA")
        setup_ha_bigip(bigip,node,float)


# Put VIPs in floating traffic group


def update_vips(bigip,bigips):
    print ("Getting list of virtual address...")
    address = bigips["address"]
    response = bigip.get("https://" + address + "/mgmt/tm/ltm/virtual-address")
    vip_list = (json.loads(response.text)["items"])
    for vip in vip_list:
        vipname = vip["name"]
        payload = {}
        payload["trafficGroup"] = "/Common/traffic-group-1"
        payload["floating"] = "enabled"
        put_resp = bigip.put("https://" + address + "/mgmt/tm/ltm/virtual-address/~Common~" + vipname,data=json.dumps(payload)).text
        put_resp = json.loads(put_resp)
        print ("VIP " + put_resp["name"] + " has been updated")
    print ("VIP update complete")


for node in bigips:
    if node["node"] == 1:
        create_trust(bigip,node)
        init_sync(bigip, node)
        create_dev_group(bigip, node)
        init_sync_dg1(bigip, node)
        update_vips(bigip,node)
        print ("HA setup complete!")
