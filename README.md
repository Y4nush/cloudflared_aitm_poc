# cloudflared_aitm_poc

This repository contains a Proof of Concept (PoC) for an **Adversary-in-the-Middle (AiTM)** attack exploiting **Cloudflared replicas**. For a detailed explanation of the attack and its implications, read the full blog post:

👉 [When Replicas Go Rogue - A Deep Dive into Cloudflared Exploitation Scenarios](https://y4nush.com/posts/when-replicas-go-rogue-a-deep-dive-into-cloudflared-replicas-exploitation-scenarios/)

## Usage

Clone the repository:
```bash
git clone https://github.com/Y4nush/cloudflared_aitm_poc.git
cd cloudflared_aitm_poc
```

Run the installation script (⚠️ Warning: Running this will automatically create and run a tunnel, which could cause availability issues):

```bash
sudo bash install.sh
Please enter your Cloudflare Tunnel token: eyJ......
```
## Commands
```bash
-------------------------------------
Available Commands and Their Usage:
-------------------------------------
sudo systemctl stop cloudflared.service && sudo pkill -f aitm.py  # Stops the aitm.py server and the tunnel.

sudo bash install.sh --run  # Runs aitm.py with the previous arguments.

python3 aitm/hijack.py list # Lists all intercepted requests.

python3 aitm/hijack.py poc <session number> # Sends a GET request with hijacked credentials as a PoC.
```
## Environment
Tested on Ubuntu 22.04.5 LTS

<img src="https://github.com/user-attachments/assets/abf5c575-d493-4820-b85b-45e8cb0162fc" alt="image" width="75"/>

