import sys
from os import path
import requests  # Import the requests library for sending HTTP requests

message = ""


def load_send():
    cur_path = path.abspath(path.dirname(__file__))
    if path.exists(cur_path + "/notify.py"):
        try:
            from notify import send
            return send
        except ImportError:
            return False
    else:
        return False


# Using ipify API to get the public IP address
def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org")
        if response.status_code == 200:
            return response.text  # Return the IP address
        else:
            return "Unable to retrieve IP"
    except requests.RequestException:
        return "Unable to retrieve IP"


# Check if login result is successful
def is_login_successful(login_result):
    return login_result == 1  # Assumption: 1 means success


def main(login_results):
    global message
    public_ip = get_public_ip()  # Get the public IP address
    for result in login_results:
        try:
            username, panel, login_result_str = result.split(":")
            login_result = int(login_result_str)

            # Check if login was successful
            if is_login_successful(login_result):
                message += f"User: {username} successfully logged into the panel: {panel}, IP: {public_ip}\n"
            else:
                message += f"User: {username} failed to log into the panel: {panel}, IP: {public_ip}\n"

        except ValueError:
            # Handle cases where the input format is incorrect
            message += f"Invalid result format for: {result}\n"

    send = load_send()
    if callable(send):
        send("serv00&ct8", message)
    else:
        print("\nFailed to load notification service")


if __name__ == "__main__":
    login_results = sys.argv[1:]
    main(login_results)
