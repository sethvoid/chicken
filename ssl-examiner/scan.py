import sys
import ssl
import socket
import json
from datetime import datetime


if len(sys.argv) < 2:
    print("\033[0;31m" + 'Missing argument <url>' + "\033[0m")
    sys.exit()

target = sys.argv[1]
verify_peer = '--verify-peer' in sys.argv
verbose_output = '--vvv' in sys.argv
red = "\033[0;31m"
green = "\033[0;32m"
reset = "\033[0m"

def curl_req(url, verify_peer):
    hostname = url.split("://")[-1].split(":")[0]
    context = ssl.create_default_context()
    ssl_socket = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
    try:
        ssl_socket.connect((hostname, 443))
        ssl_cert = ssl_socket.getpeercert()
        # Extracting commonName if present
        common_name = ""
        subject = ssl_cert.get("subject", [])
        if isinstance(subject, list):
            for name, value in subject:
                if name == "commonName":
                    common_name = value
                    break

        issuer = ssl_cert.get("issuer", ())
        primary_issuer = ""
        if isinstance(issuer, tuple):
            for name, value in issuer:
                if name == "C":
                    primary_issuer = value
                    break

        ssl_cert_details = {
            "commonName": common_name,
            "validFrom_time_t": datetime.strptime(ssl_cert["notBefore"], "%b %d %H:%M:%S %Y %Z").timestamp(),
            "validTo_time_t": datetime.strptime(ssl_cert["notAfter"], "%b %d %H:%M:%S %Y %Z").timestamp(),
            "primary_issuer": primary_issuer,
        }
        return ssl_cert_details
    finally:
        ssl_socket.close()


ssl_certificate_details = curl_req(target, verify_peer)
valid = ssl_certificate_details['validFrom_time_t']
expires = ssl_certificate_details['validTo_time_t']
issuer = ssl_certificate_details['issuer']  # C, O, CN

if verbose_output:
    print(json.dumps(ssl_certificate_details, indent=4))

name = ssl_certificate_details['commonName']

json_data = {
    'name': name,
    'expires': datetime.fromtimestamp(expires).strftime('%H:%M:%S %d-%m-%Y'),
    'issued': datetime.fromtimestamp(valid).strftime('%H:%M:%S %d-%m-%Y'),
    'primary_issuer': issuer['C'],
    'secondary_issuer': issuer['O'],
    'ca_issuer': issuer['CN']
}

with open('report-' + name + '.txt', 'w') as report_file:
    json.dump(json_data, report_file)

print(green + 'Successfully saved to: report-' + name + '.txt' + reset)

if datetime.now().timestamp() > expires:
    print(red + 'SSL cert has expired' + reset)
else:
    print(green + 'SSL is valid' + reset)

print()