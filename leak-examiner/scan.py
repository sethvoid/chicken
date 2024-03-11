import re
import json
import sys
import requests
import re

def extract_comments(content, url=""):
    html_comments = {}
    js_comments = {}

    # Extract HTML comments
    html_pattern = r"<!--(.*?)-->"
    for match in re.finditer(html_pattern, content, re.DOTALL):
        comment = match.group(1).strip()
        html_comments[match.start() + 1] = f"{url} {comment}" if url else comment

    # Extract JavaScript comments
    js_pattern = r"//(.*?)$|/\*(.*?)\*/"
    for script_match in re.finditer(r"<script\b[^>]*>(.*?)</script>", content, re.DOTALL | re.IGNORECASE):
        script_comments = {}
        script_content = script_match.group(1)
        for line_number, line in enumerate(script_content.splitlines(), start=1):
            for match in re.finditer(js_pattern, line):
                comment = match.group(1) or match.group(2)
                script_comments[line_number] = comment.strip()
        js_comments[script_match.start() + len("<script>")] = script_comments

    return {"html": html_comments, "js": js_comments}


def scan_for_prohibited(comments_html, comments_js):
    prohibited_findings = {}
    try:
        with open("prohib.json", "r") as f:
            prohibited_words = json.load(f)
    except FileNotFoundError:
        print("Error: Could not find prohib.json file")
        return prohibited_findings

    for value in prohibited_words:
        for line_number, comment in comments_html.items():
            if value.lower() in comment.lower():
                prohibited_findings[line_number] = f"PROHIBITED VALUE ({value}) in comment {comment}"

        for script_location, script_comments in comments_js.items():
            for line_number, comment in script_comments.items():
                if value.lower() in comment.lower():
                    # Adjust line number to reflect location within script block
                    prohibited_findings[script_location + line_number - 1] = f"PROHIBITED VALUE ({value}) in comment {comment}"

    return prohibited_findings

def main():
    if len(sys.argv) < 2:
        print("Usage: scan.py <url>")
        exit(1)

    url = sys.argv[1]
    try:
        content = requests.get(url).text
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not retrieve content from URL: {e}")
        exit(1)

    extracted_comments = extract_comments(content, url)
    html_comments = extracted_comments["html"]
    js_comments = extracted_comments["js"]

    if html_comments:
        print("\nComments discovered (html):")
        for line_number, comment in html_comments.items():
            print(f"[{line_number}] {comment}")

    if js_comments:
        print("\nComments discovered (JS):")
        for script_location, script_comments in js_comments.items():
            for line_number, comment in script_comments.items():
                print(f"[Script location: {script_location + 1}, Line: {line_number}] {comment}")

    prohibited_findings = scan_for_prohibited(html_comments, js_comments)
    if prohibited_findings:
        print("\n**************** PROHIBITED COMMENTS DISCOVERED ****************")
        for line_number, message in prohibited_findings.items():
            print(message)

if __name__ == "__main__":
    import requests  # You may need to install the requests library
    main()
