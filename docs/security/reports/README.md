# Security Reports (Local Artifacts)

This folder is used to store locally-generated security scan outputs (SAST/DAST/dependency/secret scans).

By default, JSON outputs in `docs/security/reports/*.json` are **gitignored** to avoid accidentally committing
content that may include sensitive strings (even when tools redact secrets).

Recommended workflow:
- Run the scans locally.
- Review the JSON reports here.
- Commit only human-readable summaries (Markdown) and any necessary code fixes.

