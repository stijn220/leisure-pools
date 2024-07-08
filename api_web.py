from flask import Flask, render_template, jsonify, request
import requests

app = Flask(__name__)

ip = '192.168.178.252'
LOGIN_URL = f"http://{ip}/cgi/login"
LIGHTS_ON_PRESS_URL = f"http://{ip}/cgi/writeTags.json?n=1&t1=bLightsON.0&v1=1&nocache=1"
LIGHTS_ON_RELEASE_URL = f"http://{ip}/cgi/writeTags.json?n=1&t1=bLightsON.0&v1=0&nocache=1"
LIGHTS_OFF_URL = f"http://{ip}/cgi/writeTags.json?n=1&t1=nLichtKleur.-1&v1=0&nocache=1"

username = "admin"
password = "admin"
session = None

def login():
    global session
    session = requests.Session()
    login_payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": f"http://{ip}",
        "Referer": f"http://{ip}/public/_weblogin.html",
    }
    response = session.post(LOGIN_URL, data=login_payload, headers=headers)
    if response.status_code == 200:
        print("Login successful")
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        session = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lights/on/press', methods=['POST'])
def lights_on_press():
    if session:
        response = session.get(LIGHTS_ON_PRESS_URL)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Lights on press"})
        else:
            return jsonify({"status": "error", "message": "Failed to send lights on press"}), 500
    return jsonify({"status": "error", "message": "No active session"}), 500

@app.route('/lights/on/release', methods=['POST'])
def lights_on_release():
    if session:
        response = session.get(LIGHTS_ON_RELEASE_URL)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Lights on release"})
        else:
            return jsonify({"status": "error", "message": "Failed to send lights on release"}), 500
    return jsonify({"status": "error", "message": "No active session"}), 500

@app.route('/lights/off', methods=['POST'])
def lights_off():
    if session:
        response = session.get(LIGHTS_OFF_URL)
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Lights off"})
        else:
            return jsonify({"status": "error", "message": "Failed to send lights off"}), 500
    return jsonify({"status": "error", "message": "No active session"}), 500

if __name__ == '__main__':
    login()
    app.run(debug=True, host='0.0.0.0', port=5000)
