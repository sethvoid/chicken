import sys
import socket
import ssl
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
text_art = '''
                ▒▒▒▒▒▒▒█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
                ▒▒▒▒▒▒▒█░▒▒▒▒▒▒▒▓▒▒▓▒▒▒▒▒▒▒░█
                ▒▒▒▒▒▒▒█░▒▒▓▒▒▒▒▒▒▒▒▒▄▄▒▓▒▒░█░▄▄
                ▒▒▄▀▀▄▄█░▒▒▒▒▒▒▓▒▒▒▒█░░▀▄▄▄▄▄▀░░█
                ▒▒█░░░░█░▒▒▒▒▒▒▒▒▒▒▒█░░░░░░░░░░░█  <scanning since 2013>
                ▒▒▒▀▀▄▄█░▒▒▒▒▓▒▒▒▓▒█░░░█▒░░░░█▒░░█
                ▒▒▒▒▒▒▒█░▒▓▒▒▒▒▓▒▒▒█░░░░░░░▀░░░░░█
                ▒▒▒▒▒▄▄█░▒▒▒▓▒▒▒▒▒▒▒█░░█▄▄█▄▄█░░█
                ▒▒▒▒█░░░█▄▄▄▄▄▄▄▄▄▄█░█▄▄▄▄▄▄▄▄▄█
                ▒▒▒▒█▄▄█░░█▄▄█░░░░░░█▄▄█░░█▄▄█
'''


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

def save_to_log(result, file_name):
    with open(file_name, 'a') as f:
        log_entry = f"{result['subject']}," \
                    f'"{result["issuer"]}","{result["from"]}","{result["to"]}"\n'
        f.write(log_entry)

def main(text_art):
    print(text_art)

    if len(sys.argv) < 2:
        print("Usage: python3 scan.py <url> <options>")
        return

    if '--help' in sys.argv:
        print("================ SSL SCANNER =================")
        print("Usage: python3 scan.py <url> <options>")
        print("Options: --help, --output-file")
        print("==============================================")
        return

    output_file = False

    if "--output-file" in sys.argv:
        output_file = True

    hostname = sys.argv[1]
    try:
        cert = get_ssl_certificate(hostname)
        print("\nSSL Certificate Details for", hostname)
        print_certificate_details(cert)
        if output_file:
            current_datetime = datetime.now()
            file_name = current_datetime.strftime("%H%M-%d-%m-%Y") + '-' + hostname + '-ssl-results.log'
            save_to_log({'subject': cert.subject.rfc4514_string(), 'issuer': cert.issuer.rfc4514_string(), 'from': cert.not_valid_before, 'to': cert.not_valid_after}, file_name)

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main(text_art)
