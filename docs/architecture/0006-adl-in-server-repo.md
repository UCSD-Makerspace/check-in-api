# Architectural Decision Log in Server Repository

## Status

Approved

## Context

These log files are relevant to both the frontend and the backend but splitting them between the two repositories would be difficult as many involve both, and it would also make it harder to access this full repository. I (Timothy) also cannot come up with a clean solution for the decisions that equally involve both repositories. I recognize that some of these files are relevant only to the client, but I find this downside incomparably less bad than splitting them between repositories.

While it is technically possible to include these documents anywhere, such as in Google Drive (this idea was briefly entertained), I believe it is important this documentation is kept as close to the source code as possible, to improve any hopes of it maintaining its relevance.

## Decision

The architecture decision records will be stored in the server repo only.

## Consequences

