# Containerization With Custom Docker Image

## Status

Accepted

## Context

The check-in system relies heavily on the current state of the kiosks/local development, resulting in frequent occasions where the development environment differs completely from kiosks, or where one kiosk differs the other.

It is also unknown exactly how the check-in deployments outside the Makerspace will be operated going forward, and containerizing would likely help improve the application portability, compatibility, and stability.

## Decision

Both the frontend and the backend will be placed into custom Docker containers built automatically as decided in [0003-cicd-pipeline](0003-cicd-pipeline.md).

## Consequences

