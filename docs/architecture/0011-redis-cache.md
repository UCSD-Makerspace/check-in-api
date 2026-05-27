# In-Memory Redis Cache

## Status

Accepted

## Context

Google Sheets API is incredibly slow to access data from so a cache is absolutely necessary for user UI interactions.

## Decision

We decided to use Redis.

## Consequences

The previous implementation used a JSON file as a cache (which had many issues), though thinking back now these issues might have all been solvable by just keeping the object in memory instead of writing it to a file.