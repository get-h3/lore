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
   point in the system's history. The shipped `lore validate` lint proves
   commands parse and answer — by default in plan mode (nothing is executed),
   with the opt-in `--execute` flag actually running gate-approved read-only
   commands and flipping drifted runbooks to `status: stale` with a drift
   reason. That lint cannot prove recovery succeeds, and it is not operator
   attestation: no shipped check attests that an operator ran a runbook
   against a live incident and the recovery worked — that attestation path
   remains unimplemented. Every runbook carries that honesty label. Treat any
   runbook command the way you would treat a command from a stranger's gist:
   read it, understand what it touches, then decide.

2. **Read-only / verify-mode by design intent.** `lore validate` holds itself
   to the same rule: even with `--execute` it runs only gate-approved
   read-only commands (`--verify` flags, `--dry-run`, SELECT-only queries);
   the default is plan-only. Commands written into runbooks should be the
   *diagnostic* form of an action, not the destructive form. If a runbook
   step mutates state, that belongs on the recovery ladder behind a human
   decision — not in an auto-validated check.

3. **Never commit a command that embeds a secret.** Runbooks are public
   material by default. A command that had to carry a token, key, or
   credential to run does not belong in a runbook in that form — write the
   command with the secret loaded from the environment (or a vault lookup)
   instead. Reviewers and absorbers (planned) should reject any proposal whose
   evidence blocks contain a live secret.