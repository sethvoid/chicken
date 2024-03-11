import sys
import socket
import ssl
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend

def get_ssl_certificate(hostname):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((hostname, 443)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            der_cert = ssock.getpeercert(binary_form=True)
            cert = x509.load_der_x509_certificate(der_cert, default_backend())
            return cert

def print_certificate_details(cert):
    print("Subject:", cert.subject.rfc4514_string())
    print("Issuer:", cert.issuer.rfc4514_string())
    print("Valid From:", cert.not_valid_before)
    print("Valid To:", cert.not_valid_after)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scan.py <url>")
        return

    hostname = sys.argv[1]
    try:
        cert = get_ssl_certificate(hostname)
        print("\nSSL Certificate Details for", hostname)
        print_certificate_details(cert)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
