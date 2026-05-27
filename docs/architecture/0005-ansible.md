# Ansible Setup Scripts

## Status

Accepted

## Context

As mentioned in [0000-context](0000-context.md), the check-in system had no method of being reinstalled from scratch and no staff were will around who had been apart of the last fresh install.

Some of the recent changes that have been made to the system also introduce more setup work that needs to be done in a consistent manner in future fresh installs.

## Decision

As such, ansible will be employed to keep the [setup instructions](../../setup.md) concise and reduce the chance of human error. Ansible also provides a reasonable degree of idempotency (the scripts can all be run whenever however many times and should always leave the servers in the same state) which is also ideal for keeping the kiosks and server in sync with the ansible scripts. This parity also allows for the ansible scripts to be a full description of how and exactly what additional configuration is required to set a machine up, instead of passing this down orally.

## Consequences

