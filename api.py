import requests
import time

ip = '192.168.178.252'

# Endpoint URLs
LOGIN_URL = f"http://{ip}/cgi/login"
WRITE_TAGS_URL = f"http://{ip}/cgi/writeTags.json"
GET_PROPERTIES_URL = f"http://{ip}/cgi/getProperties"

# Credentials
username = "admin"
password = "admin"

session = requests.Session()

# Login function
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

# Function to send GET request to writeTags.json endpoint
def send_request(action, value):
    params = {
        'n': 1,
        't1': action,
        'v1': value,
        'nocache': int(time.time() * 1000)  # Using timestamp as nocache value
    }
    try:
        response = session.get(WRITE_TAGS_URL, params=params)
        response.raise_for_status()
        print(f"Action '{action}' with value '{value}' sent successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")

# Function to turn on the lights
def turn_on_lights():
    send_request('bLightsON.0', 1)
    send_request('bLightsON.0', 0)

# Function to turn off the lights
def turn_off_lights():
    send_request('nLichtKleur.-1', 0)

# Function to open the cover
def open_cover():
    send_request('bOpenCover.0', 1)

# Function to close the cover
def close_cover():
    send_request('bCloseCover.0', 1)

# Example usage:
if __name__ == "__main__":
    # Login to establish session
    login()
    # Turn on the lights
    turn_on_lights()

    # # Wait or perform other actions...

    # # Turn off the lights
    #turn_off_lights()

    # # Wait or perform other actions...

    # # Open the cover
    #open_cover()

    # # Wait or perform other actions...

    # # Close the cover
    close_cover()

    # # Close the session
    session.close()
