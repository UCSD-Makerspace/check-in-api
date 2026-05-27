# Google Sheets Alternatives

## Status

Rejected

## Context

I (Timothy) have been somewhat frustrated by the limitations of using Google Sheets as the primary database for our systems, primarily because the system for giving access control to machines (checking checkboxes and waiting for several seconds for the script to run) is not very responsive and prone to errors due to the nature of Google Sheets.

Despite this, using Google does make the interface easy for student workers to pick up, as virtually everyone has worked with Google Sheets at least a few times in their life. In addition, hosting the primary Database on Google also eliminates another SaaS that we would otherwise have to depend on for off site backups of our data (we already use Google for several other uses).

No solutions have been discussed in extensive depth, but we've thrown around hosting our own databases and building out another tool to interface with them. I also believe there are existing database interfaces we could use but I haven't taken the time to research them and I'm not convinced they would work for our particular use case (needing to be simple and intuitive for non-programmers to interact with).

## Decision

Due to our current time constraints and priorities combined with the alternative solutions coming with their own drawbacks we've decided for now it is not worth it to modify this part of the check-in system.

## Consequences

