# Setup

In order to increase the repeatability of the setup, the entire process is outlined here and 90% of it will be completed by automatic (and at least semi-idempotent) Ansible scripts. This setup assumes that the server is being installed to an x86 computer, and that the kiosks are being installed to Raspberry Pi Keyboards. The scripts and application could be adjusted to work with other setups but would require some modification.

**IMPORTANT NOTE:** The setup currently requires Tailscale to function. As this is likely an ephemeral part of the system as I await having a functional public ip & port to run Netbird off of these docs will fail to mention the tailscale dashboard + token + local prereq steps needed for setup.

## Prerequisites (local machine)

- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/)

---

## Instructions

### Step 1: Initial Setup

#### Server:

1. Install **Ubuntu Server 24.04** with the user `makeradmin` and the hostname `ms-server`.
   1. Ensure the server is connectable via SSH and that sudoing does not require a password (likely all default, unlike for the client in step 2).
2. Connect to **UCSD-DEVICE** Wi-Fi.

#### Kiosk:

1. Install **Ubuntu Desktop 24.04** on the Pi Keyboard using **Raspberry Pi Imager** with the following config options:
  - Name: `John Makerspace`
  - Computer's Name: `ms-kiosk-x` (where x is the kiosk number)
  - Username: `makeradmin`
  - `Log in automatically` (shouldn't matter which option is selected here because the Ansible script should enable automatic logins anyway though)

2. Connect to **UCSD-DEVICE** Wi-Fi.

3. **Install SSH:**

```bash
sudo apt install openssh-server
```

4. **Allow Passwordless sudo:**

```bash
echo "makeradmin ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/makeradmin
```

5. **Add Local SSH Key to Kiosk:**
```bash
ssh-copy-id makeradmin@<kiosk_ip>
```

### Step 2: Setup Ansible Secrets

Copy `secrets.example.yml` → `secrets.yml` into the makerspace inventory and fill in the secrets.

Run the following command to encrypt the secrets:
```bash
ansible-vault encrypt secrets.yml
```

### Step 3: Check Connection

First join your local device to the **UCSD-DEVICE** Wi-Fi network.

Then, verify Ansible can reach the server and all kiosks before running any playbooks using the following command (**all ansible commands should be run from the ansible/ directory**):

```bash
ansible all -m ping -e 'ansible_host={{ lan_ip }}'
```

Note: Ansible will be unable to ping any server which you have not SSH'ed into at least once first to confirm the fingerprint, make sure you have done this.

### Step 4: Run unattended-upgrade (Server + Kiosk)

Unattended upgrade will likely hold the package lock for a substantial period of time on its first run, so if installing the check-in system shortly after installing the OS, it is best to run this manually and wait for its completion.

```bash
sudo apt update && sudo unattended-upgrade -v
```

### Step 5: Run Ansible

```bash
ansible-playbook setup.yml --ask-vault-pass
```
