# F5 HA SETUP

This project helps setup a secondary F5 as an HA pair. Each F5 must already have basic network connectivity and be licensed. The script will also put all VIPs in a floating traffic group.

## Getting Started

* This was created using python3.6
* There is an example script called f5-ha-script.py
* This is what the f5-jinja.py script will create based on data in the f5vars.csv file
* To begin, edit the f5vars.csv file with the values for your environment
* Run the f5-jinja.py file
* Run the f5-ha-script.py file

## Modifying the number of Floating IPs:

There is a dictionary called float like this:

```
float = []
float.append({"name":"Internal-Float","address":"{{ float_internal }}","vlan":"internal"})
float.append({"name":"DMZ-Float","address":"{{ float_dmz }}","vlan":"dmz"})
```

If you have more VLANs than this just add a new line to append the floating IPs and then update the f5vars.csv with the name and value:

Example:

```
float = []
float.append({"name":"Internal-Float","address":"{{ float_internal }}","vlan":"internal"})
float.append({"name":"DMZ-Float","address":"{{ float_dmz }}","vlan":"dmz"})
float.append({"name":"DMZ2-Float","address":"{{ float_dmz2 }}","vlan":"dmz2"})
```

Then just add the column and value to the f5vars.csv file.
