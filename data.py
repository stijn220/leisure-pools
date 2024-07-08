import requests
import json
import time
from sseclient import SSEClient

# Function to perform login and return session cookies
def perform_login(username, password):
    url = 'http://192.168.178.252/cgi/login'  # Replace with actual login endpoint
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = {
        'username': username,
        'password': password
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print("Login successful")
        return response.cookies  # Return cookies to maintain session
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        return None

# Function to listen to SSE events
def listen_to_sse(cookies):
    try:
        ip = '192.168.178.252'
        sse_url = f"http://{ip}/cgi/sse"
        
        messages = SSEClient(sse_url, cookies=cookies)  # Pass cookies to SSEClient
        
        for msg in messages:
            if msg.event == "error":
                print(f"Received SSE error event: {msg.data}")
            elif msg.data.startswith("S_OK"):
                print("Received SSE data:")
                try:
                    tags = msg.data.split('\n')[1]
                    tags_json = json.loads(tags)
                    for tag in tags_json:
                        print(f"{tag['n']}: {tag['v']['v']} ({tag['v']['ts']})")
                except Exception as e:
                    print(f"Error parsing SSE data: {e}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error in SSE connection: {e}")
    except Exception as e:
        print(f"Unknown error in SSE connection: {e}")

def main():
    # Replace with your actual username and password
    username = 'admin'
    password = 'admin'

    # Perform login to obtain session cookies
    cookies = perform_login(username, password)

    if cookies:
        # Start listening to SSE events with the obtained session cookies
        listen_to_sse(cookies)
    else:
        print("Login failed, cannot start SSE connection.")

if __name__ == "__main__":
    main()
