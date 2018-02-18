
import datetime
import sys, os
import jinja2
import csv

in_file="f5vars.csv"
jinja_template = "f5-ha-templ.py"
env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="."))

with open(in_file, "r") as FD:
    reader = csv.DictReader(FD)
    for vals in reader:
        gen_template = env.get_template(jinja_template)
        output = gen_template.render(vals)

f = open("f5-ha-script.py","w+")
f.write("# This file was generated on: " + str(datetime.datetime.now()) + "\n")
f.write(output)
f.close()
