import requests
import time

# Base URL for login and fetching data
base_url = "http://192.168.178.252/cgi"
login_url = f"{base_url}/login"
sse_url = f"{base_url}/sse"

# Function to perform login and return a session
def login(username, password):
    login_data = {
        'username': username,
        'password': password
    }

    try:
        session = requests.Session()
        login_response = session.post(login_url, data=login_data)
        login_response.raise_for_status()  # Raise exception for bad status codes
        print("Login successful")
        return session
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        return None

# Function to fetch and print data from the SSE endpoint
def fetch_data(session, id_param, params=None):
    url = f"{sse_url}?id={id_param}"
    if params:
        url += '&' + '&'.join(f'{key}={value}' for key, value in params.items())
    
    try:
        response = session.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        data = response.json()
        print(f"Data from {url}:")
        print(data)
        print("\n")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}\n")

# Example usage with dynamically generated ID
if __name__ == "__main__":
    username = 'admin'
    password = 'admin'
    
    # Perform login
    session = login(username, password)
    
    if session:
        current_time = int(time.time() * 1000)  # Convert current time to milliseconds
        id_params = [
            {"id": current_time},
            {"id": current_time, "na": "*"},
            {"id": current_time, "ng": 1, "g0": "Home%40%24GroupSubscrWgt%40%240"},
            {"id": current_time, "nt": 4, "t0": "nCurrentPage", "t1": "nPageRequest", "t2": "bChangeClock", "t3": "M704"}
        ]
        
        for params in id_params:
            fetch_data(session, params['id'], params)
    else:
        print("Login failed. Exiting script.")
