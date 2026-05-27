# CI/CD Pipeline and Production Deployment

## Status

Accepted

## Context

The frontend and backend use custom images for their own deployment, and there needs to be a way for those images to be built automatically to allow for continuous deployment. I (Timothy) initially tested this using Kubernetes (K3s), though there was reasonable concern that this would be unsustainable for future developers to maintain as this is not a reasonable skill to expect developers to have.

Additionally, David holds a strong opinion that continuous deployment should not be necessary, while I have a strong bias towards supporting it, both of these definitely weighed into our decision.

## Decision

We decided the production environment for both the frontend and backend will be deployed via Docker Compose. Though Docker Compose is not the most production ready tool, this is not the most complicated environment we're deploying to, and it meets a reasonable middle ground between supporting automatic deployment and being easy to learn to use.

The docker compose script will be deployed via the ansible scripts ([0005-ansible](0005-ansible.md)) and automatic image updating will be handled by [watchtower](https://github.com/nicholas-fedor/watchtower). watchtower is also not designed for production environments, but with the reasonably low stakes at play here we've decided that this is a great solution that does what we want while maintaining simplicity.

## Consequences

