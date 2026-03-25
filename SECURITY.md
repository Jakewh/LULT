# Security Policy

## Supported Versions

Security updates are provided for the latest state of the `main` branch.
Older snapshots and local forks are not guaranteed to receive fixes.

## Reporting a Vulnerability

If you discover a security issue, please report it privately first.

Preferred contact process:
1. Open a private report if your hosting platform supports it.
2. If private reporting is unavailable, create a minimal issue without exploit details and ask for a secure contact channel.
3. Include reproduction steps, affected files, and impact.

Please include:
- Project version/commit
- OS and environment details
- Exact steps to reproduce
- Expected vs actual behavior
- Any proof-of-concept (only if safe and necessary)

## Response Targets

- Acknowledgement: within 7 days
- Initial triage: within 14 days
- Fix timeline: depends on severity and complexity

## Disclosure Guidance

Please do not publish full exploit details before a fix is available.
Coordinated disclosure helps protect users.

## Scope Notes

This project can execute external tools (`mono`, `repak`, `UnrealLocres.exe`).
Security reports involving tool path handling, update checks, and process execution are in scope.
