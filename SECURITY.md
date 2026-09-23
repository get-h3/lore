# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | yes |

Earlier builds of `lore` are not supported; upgrade to the latest `0.1.x`
before reporting an issue.

## Reporting a vulnerability

Open a **private GitHub Security Advisory** against
[get-h3/lore](https://github.com/get-h3/lore) → "Report a vulnerability". This is the
supported private channel for this repository; do not file a public issue for
a suspected vulnerability.

## Threat notes specific to this tool

`lore` is a runbook compiler: the artifacts it is designed to hold contain
**operational commands** — the exact commands and queries that diagnosed real
incidents. Three rules follow, and they are part of the tool's design intent,
not boilerplate:

1. **Review before you execute.** A command in a runbook was correct *the last
   time this class of incident happened*, on a different box, at a different
   point in the system's history. Re-validation (planned, not yet implemented)
   will prove commands parse and answer — it cannot prove recovery succeeds.
   Every runbook carries that honesty label. Treat any runbook command the way
   you would treat a command from a stranger's gist: read it, understand what
   it touches, then decide.

2. **Read-only / verify-mode by design intent.** The re-validation loop is
   specified to run every runbook command in read-only/verify mode
   (`--verify` flags, `--dry-run`, SELECT-only queries). Commands written into
   runbooks should be the *diagnostic* form of an action, not the destructive
   form. If a runbook step mutates state, that belongs on the recovery ladder
   behind a human decision — not in an auto-validated check.

3. **Never commit a command that embeds a secret.** Runbooks are public
   material by default. A command that had to carry a token, key, or
   credential to run does not belong in a runbook in that form — write the
   command with the secret loaded from the environment (or a vault lookup)
   instead. Reviewers and absorbers (planned) should reject any proposal whose
   evidence blocks contain a live secret.