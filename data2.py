import requests
import json
import time

def login():
    login_payload = {
        "username": username,
        "password": password
    }
    try:
        response = session.post(LOGIN_URL, data=login_payload)
        response.raise_for_status()
        print("Login successful")
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")

def process_event(event):
    # Function to process each SSE event
    event_data = event.split('\n')
    event_dict = {}
    for line in event_data:
        if line.startswith('data:'):
            data = line[len('data:'):].strip()
            try:
                event_dict = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON data: {e}")
                event_dict = {}
    return event_dict

def get_sse_events(sse_url, cookies):
    try:
        with requests.get(sse_url, stream=True, cookies=cookies) as response:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.startswith('data:') or line.startswith('id:') or line.startswith('event:'):
                        print(line)
                        if line.startswith('data:'):
                            data = line[len('data:'):].strip()
                            print(f"Received data: {data}")
                            # Process the event data here
                            event_dict = process_event(line)
                            print(f"Parsed event data: {event_dict}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    username = 'admin'  # Replace with your actual username
    password = 'admin'  # Replace with your actual password

    # Perform login to obtain session cookies
    session_cookies = perform_login(username, password)

    if session_cookies:
        current_timestamp = int(time.time())

        sse_url = f"http://192.168.178.252/cgi/sse?id={current_timestamp}&minPeriod=100"
        
        print(f"Connecting to SSE stream at: {sse_url}")

        # Fetch and process SSE events
        get_sse_events(sse_url, session_cookies)
