#!/usr/bin/env bash
# Append a dated failure notice for lore-dep-drift.service (OnFailure target).
# Invoked by systemd; adjust the directory if HOME differs on the box.
notice_dir="${HOME}/.local/share/lore"
mkdir -p "$notice_dir"
printf '%s\n' "failure-notice: $(date +%Y-%m-%dT%H:%M:%S%z) lore-dep-drift.service failed; check journalctl --user -u lore-dep-drift.service" >> "$notice_dir/dep-drift-failures.log"
