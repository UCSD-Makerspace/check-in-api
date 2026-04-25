# Setup

This setup assumes that the server is being installed to a Raspberry Pi computer, and that the kiosks are being installed to Raspberry Pi Keyboards. The scripts and application could be adjusted to work with other setups but would require some modification.

## Prerequisites (local machine)

- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/)

---

## Instructions

### Step 1: Setup Server (Local + Server)

Install **Ubuntu Server 24.04** on the Raspberry Pi using **Raspberry Pi Imager** with the user `makeradmin` and the hostname `makerspace-server`. This should automatically set the server up to be connectable via SSH and do a lot of the configuring that is manual for the client in step 2.

### Step 2: Setup Kiosks (Local + Kiosk)

#### Install Ubuntu Desktop 24.04

Install **Ubuntu Desktop 24.04** on the Pi Keyboard using **Raspberry Pi Imager** with the following config options:
* Name: `John Makerspace`
* Computer's Name: `ms-kiosk-x` (where x is the kiosk number)
* Username: `makeradmin`
* `Log in automatically` (shouldn't matter which option is selected here because the Ansible script should enable automatic logins anyway though)

#### Connect to Wi-Fi

[//]: # (TODO: switch to fabman wifi)
Connect to **UCSD-DEVICE** with password `mkrspace`.

#### Enable SSH

```bash
sudo apt install openssh-server
```

#### Allow Passwordless sudo

```bash
echo "makeradmin ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/makeradmin
```

#### Add Local SSH Key to Kiosk
```bash
ssh-copy-id makeradmin@<kiosk_ip>
```

### Step 3: Configure Ansible Inventory (Local)

Copy `inventory.example.ini` → `inventory.ini` and fill out values.

### Step 4: Ansible Ping (Local)

Verify Ansible can reach everything before running any playbooks:

```bash
ansible -i inventory.ini all -m ping
```

### Step 5: Run unattended-upgrade (Server + Kiosk)

Unattended upgrade will likely hold the package lock for a substantial period of time on its first run, so if installing the check-in system shortly after installing the OS, it is best to run this manually and wait for its completion.

```bash
sudo apt update && sudo unattended-upgrade -v
```

### Step 6: Setup Server (Local)

Run the ansible playbook to set the server up (Docker install, SSH hardening):
```bash
ansible-playbook ansible/1-setup-server.yml
```

### Step 7: Setup Kiosks (Local)

Run the ansible playbook to set the kiosks up (Docker install, system settings, SSH hardening):
```bash
ansible-playbook ansible/2-setup-kiosks.yml
```

### Step 8 (Optional): Set Up Local WireGuard Client (Local)

Generate a WireGuard key pair for your machine and add a `[Peer]` block to `ansible/files/wireguard-peers.conf` with your public key and a unique unused IP in the `10.8.0.0/24` range:

```ini
# your name
[Peer]
PublicKey = <LOCAL_WIREGUARD_PUBLIC_KEY>
AllowedIPs = <LOCAL_WIREGUARD_IP>/32
```

After running the WireGuard ansible script, finish setting up your client's config. Here's an example config of what it might look like after setup:

```ini
[Interface]
PrivateKey = <LOCAL_WIREGUARD_PRIVATE_KEY>
Address = <LOCAL_WIREGUARD_IP>/24

[Peer]
PublicKey = <SERVER_WIREGUARD_PUBLIC_KEY>
AllowedIPs = 10.8.0.1/32
Endpoint = <SERVER_IP>:51820
PersistentKeepalive = 25

```

### Step 9: Setup WireGuard (Local)

```bash
ansible-playbook ansible/3-setup-wireguard.yml
```

Run the ansible playbook to connect the server and kiosks via WireGuard. Create your WireGuard config using the key printed at the end as SERVER_PUBLIC_KEY:
```ini
[Interface]
PrivateKey = <LOCAL_WIREGUARD_PRIVATE_KEY>
Address = <LOCAL_WIREGUARD_IP>/24

[Peer]
PublicKey = <SERVER_WIREGUARD_PUBLIC_KEY>
AllowedIPs = 10.8.0.1/32
Endpoint = <SERVER_PUBLIC_IP>:51820
PersistentKeepalive = 25
```

### Step 10: Load Secrets (Local)

Copy `secrets.example.yml` → `secrets.yml` and fill in the secrets.

Run the following command to encrypt the secrets:
```bash
ansible-vault encrypt secrets.yml
```

Then use the following ansible playbook to copy them to the server and start the stack:
```bash
ansible-playbook ansible/4-load-secrets.yml --ask-vault-pass
```