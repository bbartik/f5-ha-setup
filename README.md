# F5 HA SETUP

This project helps setup a secondary F5 as an HA pair. Each F5 must already have basic network connectivity and be licensed. The script will also put all VIPs in a floating traffic group.

## Getting Started

* This was created using python3.6
* There is an example script called f5-ha-script.py
* This is what the f5-jinja.py script will create based on data in the f5vars.csv file
* To begin, edit the f5vars.csv file with the values for your environment
* Run the f5-jinja.py file
* Run the f5-ha-script.py file
