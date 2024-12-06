from flask import Flask, request, redirect, jsonify, make_response
import logging
import os
import json
import time
import uuid
import argparse
from datetime import datetime
from urllib.parse import urlparse

app = Flask(__name__)


parser = argparse.ArgumentParser(description="Flask Redirection Server")
parser.add_argument("--application-url", required=True, help="Base URL of the target server")
parser.add_argument("--service-url", required=True, help="Service URL to determine protocol and port")
args = parser.parse_args()

# Configuration
APPLICATION_URL = args.application_url
SERVICE_URL = args.service_url
parsed_service_url = urlparse(SERVICE_URL)

# Redirection settings
REDIRECTION_TIMEOUT = 60  # Timeout for active redirection (seconds)
REDIRECTION_DELAY = 2  # Delay in seconds between redirects
MAX_REDIRECT_ATTEMPTS = 10  # Maximum number of redirects per IP

# Extract protocol, hostname, and port
HOSTNAME = parsed_service_url.hostname or "0.0.0.0"
PORT = parsed_service_url.port or (443 if parsed_service_url.scheme == "https" else 80)

# Directory to store intercepted requests
LOG_DIR = "intercepted_requests"
os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the directory exists



# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def get_client_ip():
    """Extract the client IP from the request headers."""
    if request.environ.get("HTTP_X_FORWARDED_FOR"):
        return request.environ["HTTP_X_FORWARDED_FOR"].split(",")[0]
    return request.remote_addr


def generate_redirect_token():
    """Generate a unique redirect token."""
    return str(uuid.uuid4())


def log_request(client_ip, path, method, headers, query_params, body):
    """Log intercepted request details to a file."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = {
        "timestamp": timestamp,
        "client_ip": client_ip,
        "path": f"/{path}",
        "method": method,
        "headers": headers,
        "query_params": query_params,
        "body": body,
    }
    log_filename = os.path.join(LOG_DIR, f"{timestamp}_{method}_{path.replace('/', '_')}.json")
    with open(log_filename, "w") as log_file:
        json.dump(log_entry, log_file, indent=4)
    logging.info(f"Request logged to {log_filename}")


def redirect_logic(client_ip, path, redirect_token):
    """Perform redirection logic for the given IP and path."""
    logging.info(f"Executing redirection logic for:, Path: /{path}, Redirect Token: {redirect_token}")

    # Build the target URL for Server 2
    target_url = f"{APPLICATION_URL}/{path}"

    # Simulate a delay (optional)
    logging.info(f"Delaying redirection for {REDIRECTION_DELAY} seconds.")
    time.sleep(REDIRECTION_DELAY)

    # Create a response with redirection and headers to clear cache
    logging.info(f"Redirecting client:{client_ip} to {target_url}.")
    resp = make_response(redirect(target_url, code=302))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"  # Immediately expires
    resp.set_cookie("redirect_token", redirect_token, max_age=3600)  # Preserve cookies
    return resp


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def handle_route(path):
    """Handle all routes, log the request, and redirect to Server 2."""
    client_ip = get_client_ip()
    method = request.method
    headers = dict(request.headers)
    query_params = request.args.to_dict()
    body = request.get_data(as_text=True)

    # Log the intercepted request
    log_request(client_ip, path, method, headers, query_params, body)

    # Retrieve or generate a redirect token
    redirect_token = request.cookies.get("redirect_token")
    if not redirect_token:
        redirect_token = generate_redirect_token()
        logging.info(f"Generated new redirect token: {redirect_token}")

    # Perform redirection and return the response
    return redirect_logic(client_ip, path, redirect_token)


if __name__ == "__main__":
    app.run(host=HOSTNAME, port=PORT, ssl_context="adhoc" if parsed_service_url.scheme == "https" else None)