import aiohttp
import asyncio
import time

ip = '192.168.178.252'

# Endpoint URLs
LOGIN_URL = f"http://{ip}/cgi/login"
WRITE_TAGS_URL = f"http://{ip}/cgi/writeTags.json"
GET_PROPERTIES_URL = f"http://{ip}/cgi/getProperties"

# Credentials
username = "admin"
password = "admin"

# Custom headers to mimic requests behavior
headers = {
    'User-Agent': 'Custom User-Agent',
}

# Login function
# Login function with manual cookie extraction
async def login(session):
    login_payload = {
        "username": username,
        "password": password
    }
    async with session.post(LOGIN_URL, data=login_payload, headers=headers) as response:
        if response.status == 200:
            print("Login successful")
            
            # Manually extract cookies from the response headers
            cookies = response.cookies
            if cookies:
                print(f"Cookies received: {cookies}")
                
                # Manually update the session's cookie jar
                for cookie_name, cookie_value in cookies.items():
                    session.cookie_jar.update_cookies({cookie_name: cookie_value.value})
                return cookies
            else:
                print("No cookies found in response.")
                return None
        else:
            print(f"Login failed: {response.status}")
            return None


# Function to send GET request to writeTags.json endpoint
async def send_request(session, action, value):
    params = {
        'n': 1,
        't1': action,
        'v1': value,
        'nocache': int(time.time() * 1000)  # Using timestamp as nocache value
    }
    async with session.get(WRITE_TAGS_URL, params=params, headers=headers) as response:
        if response.status == 200:
            print(f"Action '{action}' with value '{value}' sent successfully")
        else:
            print(f"Error sending request: {response.status}")
            print(await response.text())

# Example usage:
async def main():
    timeout = aiohttp.ClientTimeout(total=30)  # Adjust the timeout value as needed
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        # Login to establish session and get cookies
        cookies = await login(session)

        # Check if cookies were set and stored in the session
        if not cookies:
            print("Failed to retrieve cookies, aborting.")
            return

        # Now, manually attach cookies to subsequent requests if needed
        # You can explicitly add cookies to the session if necessary
        for cookie_name, cookie_value in cookies.items():
            session.cookie_jar.update_cookies({cookie_name: cookie_value})

        # Turn on the lights
        await send_request(session, 'bLightsON.0', 1)
        await send_request(session, 'bLightsON.0', 0)

        # Wait or perform other actions...

# Run the asynchronous tasks
if __name__ == "__main__":
    asyncio.run(main())
