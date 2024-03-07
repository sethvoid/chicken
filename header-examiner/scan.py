import sys
import re
import json
import requests
from datetime import datetime

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
print(text_art)

# ANSI escape codes for colors
red = "\033[0;31m"
green = "\033[0;32m"
reset = "\033[0m"  # Reset to default color

# Set timeout value in seconds
timeout = 10

try:
    target = sys.argv[1]
except IndexError:
     print(red + "missing argument target > span.py <target> <profile>" + reset)
     sys.exit(1)

configFile = "profile.json"

try:
    response = requests.head(target, timeout=timeout)
except requests.exceptions.Timeout:
    print(red + "--------------------------------------------ERROR------------------------------------------------" + reset)
    print(red + "Request timed out. Please check the URL and try again." + reset)
    print(red + "--------------------------------------ERROR MESSAGE ENDS-----------------------------------------" + reset)
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(red + "--------------------------------------------ERROR------------------------------------------------" + reset)
    print(red + f"{e}" + reset)
    print(red + "--------------------------------------ERROR MESSAGE ENDS-----------------------------------------" + reset)
    sys.exit(1)

headerContentArray = {}
for key, value in response.headers.items():
    headerArray = {}
    headerArray[0] = key.lower()
    headerArray[1] = value.strip().lower()
    multiValues = None
    if ',' in headerArray[1]:
        multiValues = [val.strip() for val in headerArray[1].split(',')]
    if ';' in headerArray[1]:
        multiValues = [val.strip() for val in headerArray[1].split(',')]

    if multiValues:
        headerContentArray[headerArray[0]] = multiValues
    else:
        headerContentArray[headerArray[0]] = headerArray[1]

configArray = json.load(open(configFile))

pass_result = []
fail_result = []
for test_name, test in configArray.items():
    test['key'] = test['key'].lower()
    if test['matching-type'] == 'should-not-be-set':
        if test['key'] in headerContentArray:
            fail_result.append({'name': test['key'], 'result': f"Prohibited header set {test['key']}", 'help_link': test['link']})
            continue
        else:
            pass_result.append({'name': test['key'], 'result': f"Header {test['key']} is not present", 'help_link': test['link']})
            continue

    if test['key'] not in headerContentArray:
        fail_result.append({'name': test['key'], 'result': 'Header is not set.', 'help_link': test['link']})
        continue

    if test['type'] == 'value':
        if test['matching-type'] == 'should-not-be-set':
            if test['key'] in headerContentArray:
                fail_result.append({'name': test['key'], 'result': f"Prohibited header set {test['key']}", 'help_link': test['link']})
                continue

        if test['key'] not in headerContentArray:
            fail_result.append({'name': test['key'], 'result': 'Header is not set or is missing.', 'help_link': test['link']})
            continue

        if test['matching-type'] == 'should-not-contain':
            failFlag = False
            failFlag = test['value'].lower() in headerContentArray[test['key']]

            if failFlag:
                fail_result.append({'name': test['key'], 'result': f"Header {test['key']} contains invalid value {test['value']}", 'help_link': test['link']})
                continue
        else:
            passFlag = False
            passFlag = headerContentArray[test['key']] == test['value'].lower()

            if passFlag:
                pass_result.append({'name': test['key'], 'result': f"Header {test['key']} contains correct value {test['value']}", 'help_link': test['link']})
                continue

        fail_result.append({'name': test['key'], 'result': f"Header {test['key']} contains invalid value {test['value']}", 'help_link': test['link']})

    elif test['type'] == 'multivalue':
        if test['key'] not in headerContentArray:
            fail_result.append({'name': test['key'], 'result': 'Header is not set or is missing.', 'help_link': test['link']})
            continue

        passCount = 0
        count = len(test['value'])
        for val in test['value']:
            val = val.lower()
            if test['matching-type'] == 'should-not-contain':
                if val in headerContentArray[test['key']]:
                    fail_result.append({'name': test['key'], 'result': f"Header {test['key']} contains invalid value {val}", 'help_link': test['link']})
                    continue
                passCount += 1
            else:
                if val in headerContentArray[test['key']]:
                    pass_result.append({'name': test['key'], 'result': f"Header {test['key']} contains correct value {val}", 'help_link': test['link']})
                    passCount += 1

        if passCount < count:
            fail_result.append({'name': test['key'], 'result': f"Header {test['key']} is missing some values ", 'help_link': test['link']})

# Function to save results to a log file
def save_to_log(result, file_name, status):
    with open(file_name, 'a') as f:
        log_entry = f"{status},{result['name']}," \
                    f'"{result["result"]}","{result["help_link"]}"\n'
        f.write(log_entry)

# Get the current date and time
current_datetime = datetime.now()

# Format the date and time string in the desired format
file_name = current_datetime.strftime("%H%M-%d-%m-%Y") + '-results.log'
save_to_log({'name': "scan.py", 'result': '', 'help_link': ''}, file_name, "SCRIPT:")
save_to_log({'name': target, 'result': '', 'help_link': ''}, file_name, "TARGET:")
save_to_log({'name': 'header-name', 'result': 'error', 'help_link': 'information-link'}, file_name, "result")

print(green + ' ------------------------------------ PASS --------------------------------------- ' + reset)
for p in pass_result:
    print(green + p['name'] + ' ' +p['result'] + reset)
    # Log pass results
    save_to_log({'name': p['name'], 'result': p['name'], 'help_link': p['help_link']}, file_name, "PASS")
print("\n")

if fail_result:
    print(red + ' ------------------------------------ FAIL --------------------------------------- ' + reset)
    for f in fail_result:
        print(red + f['name'] + ' ' + f['result'] + reset)
        save_to_log({'name': f['name'], 'result': f['name'], 'help_link': f['help_link']}, file_name, "FAIL")
    print("\n")

print("File has been saved as " + file_name)
if '-vvv' in sys.argv:
    print(response.headers.items())
