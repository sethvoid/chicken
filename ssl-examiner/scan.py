import sys
import socket
import datetime
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend

red = "\033[0;31m"
green = "\033[0;32m"
reset = "\033[0m"

def curl_req(url, verify_peer):
    if '://' in url:
        url = url.replace('https://', '').replace('http://', '').replace('://', '')

    try:
        with socket.create_connection((url, 443)) as sock:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=url) as ssock:
                pem_cert = ssock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(pem_cert, default_backend())
                cert_not_before = cert.not_valid_before
                cert_not_after = cert.not_valid_after
                return {
                    'commonName': cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value,
                    'validFrom_time_t': cert_not_before.timestamp(),
                    'validTo_time_t': cert_not_after.timestamp(),
                    'issuer': {
                        'C': cert.issuer.get_attributes_for_oid(x509.NameOID.COUNTRY_NAME)[0].value,
                        'O': cert.issuer.get_attributes_for_oid(x509.NameOID.ORGANIZATION_NAME)[0].value,
                        'CN': cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0].value
                    }
                }

    except Exception as e:
        print(red + f"Error: {e}" + reset)
        return None

def get_issuer_field(issuer, field):
    if issuer.get(field):
        return issuer[field][0][1]
    return ''

if len(sys.argv) < 2:
    print(red + 'Missing argument <url>' + reset)
    sys.exit()

target = sys.argv[1]
verify_peer = '--verify-peer' in sys.argv
verbose_output = '--vvv' in sys.argv

ssl_certificate_details = curl_req(target, verify_peer)
print(ssl_certificate_details)
if not ssl_certificate_details:
    sys.exit()

valid = ssl_certificate_details['validFrom_time_t']
expires = ssl_certificate_details['validTo_time_t']
issuer = ssl_certificate_details['issuer']  # C, O, CN

if verbose_output:
    print(json.dumps(ssl_certificate_details, indent=4))

name = ssl_certificate_details['subjectAltName']

json_data = {
    'name': name,
    'expires': datetime.datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z").strftime('%H:%M:%S %d-%m-%Y'),
    'issued': datetime.datetime.strptime(valid, "%b %d %H:%M:%S %Y %Z").strftime('%H:%M:%S %d-%m-%Y'),
    'primary_issuer': get_issuer_field(issuer, 'C'),
    'secondary_issuer': get_issuer_field(issuer, 'O'),
    'ca_issuer': get_issuer_field(issuer, 'CN')
}

with open('report-' + name + '.txt', 'w') as report_file:
    json.dump(json_data, report_file)

print(green + 'Successfully saved to: report-' + name + '.txt' + reset)

if datetime.datetime.now() > datetime.datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z"):
    print(red + 'SSL cert has expired' + reset)
else:
    print(green + 'SSL is valid' + reset)

print()
