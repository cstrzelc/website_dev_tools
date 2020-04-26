import csv
import os

home="/home/"

# Provision customer environment based on customers.csv
with open('customers.csv', newline='') as csvfile:
    customerfile = csv.reader(csvfile, delimiter=','):
    for customer in customerfile:
        customer_alias = customer[0]
        customer_url = customer[1]
        customer_email = customer[2]

