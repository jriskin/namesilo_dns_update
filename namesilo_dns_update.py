import requests
import xml.etree.ElementTree as ET
from tabulate import tabulate
from termcolor import colored

# Replace with your API key from Namesilo
API_KEY = 'YOURAPIKEY'

# Set your list of domains
domains = ['YOURDOMAIN.COM', 'anotherdomain.com']  # Add more domains as needed

# Set the record type you want to update
record_type = 'A'

# Namesilo API endpoints
list_records_url = 'https://www.namesilo.com/api/dnsListRecords'
update_dns_url = 'https://www.namesilo.com/api/dnsUpdateRecord'

# Get the current public IP address
def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    public_ip = response.json()['ip']
    return public_ip

# Function to list DNS records for a domain
def list_dns_records(api_key, domain):
    payload = {
        'version': '1',
        'type': 'xml',
        'key': api_key,
        'domain': domain,
    }
    response = requests.get(list_records_url, params=payload)
    return response.text

# Create a function to update the DNS record
def update_dns_record(api_key, domain, record_id, record_type, new_value):
    payload = {
        'version': '1',
        'type': 'xml',
        'key': api_key,
        'domain': domain,
        'rrid': record_id,
        'rrtype': record_type,
        'rrvalue': new_value,
    }
    response = requests.get(update_dns_url, params=payload)
    return response.text

def get_record_id(records_xml, record_type, old_ip):
    root = ET.fromstring(records_xml)
    records = root.findall(".//resource_record")

    for record in records:
        if record.find('type').text == record_type and record.find('value').text == old_ip:
            return record.find('record_id').text

    return None

def print_dns_records(records_xml, record_type):
    root = ET.fromstring(records_xml)
    records = root.findall(".//resource_record")

    headers = [colored('Record ID', 'cyan'), colored('Type', 'cyan'), colored('Value', 'cyan'), colored('TTL', 'cyan')]
    data = []
    old_ips = []

    for record in records:
        if record.find('type').text == record_type:
            record_id = record.find('record_id').text
            rtype = record.find('type').text
            value = record.find('value').text
            ttl = record.find('ttl').text
            data.append([colored(record_id, 'yellow'), colored(rtype, 'green'), colored(value, 'blue'), colored(ttl, 'magenta')])
            old_ips.append(value)

    table = tabulate(data, headers=headers, tablefmt="pretty")
    print(table)
    
    return old_ips

def print_update_response(response_xml, old_ip, new_ip):
    root = ET.fromstring(response_xml)
    code = root.find(".//code").text
    detail = root.find(".//detail").text
    
    record_id_element = root.find(".//record_id")
    if record_id_element is not None:
        record_id = record_id_element.text
    else:
        record_id = "Not found"

    headers = [colored("Code", "cyan"), colored("Detail", "cyan"), colored("Record ID", "cyan"), colored("Old IP", "cyan"), colored("New IP", "cyan")]
    data = [[colored(code, 'yellow'), colored(detail, 'green'), colored(record_id, 'blue'), colored(old_ip, 'magenta'), colored(new_ip, 'magenta', 
attrs=['bold'])]]
    table = tabulate(data, headers=headers, tablefmt="pretty")
    print(table)

# Get the current public IP address
current_ip = get_public_ip()
print(colored("Current public IP:", 'cyan'), colored(current_ip, attrs=['bold']))

# Call the function to list and update the DNS records for each domain in the list
for domain in domains:
    print(f"\nListing records for {domain}:")
    records_xml = list_dns_records(API_KEY, domain)
    old_ips = print_dns_records(records_xml, record_type)
    # Extract record IDs for records of the specified type
    root = ET.fromstring(records_xml)
    record_ids = [
        r.find('record_id').text
        for r in root.findall(".//resource_record")
        if r.find('type').text == record_type
    ]

    # Call the function to update the DNS record for each record ID with the current public IP address
    for idx, old_ip in enumerate(old_ips):
        record_id = get_record_id(records_xml, record_type, old_ip)
        print(f"\nUpdating {domain} with record ID {record_id}:")
        response = update_dns_record(API_KEY, domain, record_id, record_type, current_ip)
        print_update_response(response, old_ip, current_ip)
