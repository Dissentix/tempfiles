#!/usr/bin/env python3
import sys, os, subprocess
from urllib.parse import urlparse, urlsplit

def run_command_in_bash(command):
    try:
        result = subprocess.run(["bash", "-c", command], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{colors.RED}Error occurred:{colors.RED} {result.stderr}")
            return False
        return result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        print(f"{colors.RED}Status : FAIL{colors.RED} {exc.returncode} {exc.output}")

class colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GRAY = "\033[90m"

def get_hostname(url):
    if url.startswith('http'):
        url_components = urlsplit(url)
        return url_components.netloc
    else:
        return url

def good_url(url):
    extensions = ['.json', '.js', '.fnt', '.ogg', '.css', '.jpg', '.jpeg', '.png', '.svg', '.img', '.gif', '.exe', '.mp4', '.flv', '.pdf', '.doc', '.ogv', '.webm', '.wmv', '.webp', '.mov', '.mp3', '.m4a', '.m4p', '.ppt', '.pptx', '.scss', '.tif', '.tiff', '.ttf', '.otf', '.woff', '.woff2', '.bmp', '.ico', '.eot', '.htc', '.swf', '.rtf', '.image', '.rf', '.txt', 'xml', 'zip']
    try:
        parsed_url = urlparse(url)
        for ext in extensions:
            if (parsed_url.path).endswith(ext):
                return False
        return True
    except Exception as e:
        print(f"{colors.RED}Error: {str(e)}{colors.RED}")
        return None

def finalize(domain):
    unique_lines = set()
    for file_path in [f"{domain}.waybackurls", f"{domain}.gau"]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                for line in file:
                    if good_url(line):
                        unique_lines.add(line.strip())
    unique_lines = {value for value in unique_lines if value}
    if len(unique_lines) == 0:
        return False
    with open(f"{domain}.passive", 'w') as file:
        for element in unique_lines:
            file.write(str(element) + '\n')
    return unique_lines

def is_file(filepath):
    return os.path.isfile(filepath)

def run_nice_passive(domain):
    print(f"{colors.BLUE}Gathering URLs passively for: {domain}{colors.BLUE}")
    
    # Commenting out the waybackurls command (disabling it):
    # f"timeout 120s bash -c 'echo {domain} | waybackurls | sort -u | anew {domain}.waybackurls'"
    
    commands = [
        f"gau {domain} --threads 1 --subs | anew {domain}.gau"
    ]
    
    for command in commands:
        print(f"{colors.BLUE}Executing command: {command}{colors.BLUE}")
        run_command_in_bash(command)
    
    print(f"{colors.BLUE}Merging results for: {domain}{colors.BLUE}")
    res = finalize(domain)
    res_num = len(res) if res else 0
    print(f"{colors.GREEN}Done for {domain}, results: {res_num}{colors.GREEN}")

def get_input():
    if not sys.stdin.isatty():
        return sys.stdin.readline().strip()
    elif len(sys.argv) > 1:
        return sys.argv[1]
    else:
        return None

if __name__ == "__main__":
    input = get_input()
    if input is None:
        print(f"{colors.YELLOW}Usage: echo domain.tld | nice_passive{colors.YELLOW}")
        print(f"{colors.YELLOW}Usage: cat domains.txt | nice_passive{colors.YELLOW}")
        sys.exit()
    
    if is_file(input):
        with open(input, 'r') as file:
            for line in file:
                domain = get_hostname(line)
                run_nice_passive(domain)
    else:
        run_nice_passive(get_hostname(input))
