# WireGuard VPN

## Status

Accepted

## Context

It is important that any communications involving student data be as secure as possible. With it in mind that this system is likely to get passed from student worker to student worker I (Timothy) want the security to be something that would be difficult to accidentally defeat. I believe WireGuard is a good solution to this problem as it handles encrypting all network traffic and a misconfigured setup is substantially less likely to compromise student data. Ansible will be responsible for setting up nearly the entire network, which will further reduce the likelihood of a misconfiguration.

In brief, I also want to mention the other solutions we considered. One solution would be to put the service on a VLAN so all communication is internal, though this would likely complicate getting a setup working for the SIO Makerspace (something we intend to still support as of now, although Mark is against it). On the opposite end we could also expose the service publicly, although this is the exact sort of thing that both David and I think is an unnecessary risk to take when the API is only used internally by the check-in system (by that I mean no end users actually use the service, they merely interface with the check-in kiosk). SSH tunnels were dismissed as they establish tunnels similar to WireGuard but have their own overhead and also expose the server as all kiosks would need SSH access. Tailscale was considered (it is based on WireGuard) but once [0009-server-static-ip](0009-server-static-ip.md) is implemented we believe its benefits are no longer worth the drawback of adding another SaaS dependency (WireGuard itself is an open source protocol).

## Decision

A peer-to-peer WireGuard network will be established that allows secure communication between each kiosk and the server.

## Consequences

