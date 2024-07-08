import requests

ip = '192.168.178.252'
base_url = f"http://{ip}/cgi/"
common_endpoints = [
    "login",
    "logout",
    "status",
    "control",
    "writeTags.json",
    "readTags.json",
    "getStatus.json"
]

def check_endpoints():
    found_endpoints = []
    for endpoint in common_endpoints:
        url = base_url + endpoint
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Found: {url}")
            found_endpoints.append(url)
        else:
            print(f"Not found: {url}")
    return found_endpoints

found_endpoints = check_endpoints()
print("Found endpoints:", found_endpoints)
