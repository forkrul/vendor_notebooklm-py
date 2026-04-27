#!/usr/bin/env bash
#
# Fetch the latest from upstream (teng-lin/notebooklm-py) and rebase the local
# main onto it, then push to the forkrul fork. Read-only against origin.
#
# Conventions follow forkrul/domains: logs to stderr, data to stdout, --dry-run
# supported, exit 0/1/2 = success/error/warning.

set -euo pipefail

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") [--dry-run]

Fetch upstream (origin), rebase main onto origin/main, push to forkrul.
Refuses to run if origin's pushurl is anything other than 'no_push'.
EOF
      exit 0
      ;;
    *) echo "Unknown arg: $arg" >&2; exit 1 ;;
  esac
done

log() { echo "[sync] $*" >&2; }

# Safety: origin must be fetch-only.
push_url=$(git config --get remote.origin.pushurl || echo "")
if [[ "$push_url" != "no_push" ]]; then
  log "ERROR: remote.origin.pushurl is '$push_url', expected 'no_push'."
  log "Run:   git remote set-url --push origin no_push"
  exit 1
fi

# Safety: forkrul remote must exist.
if ! git remote get-url forkrul >/dev/null 2>&1; then
  log "ERROR: 'forkrul' remote is not configured."
  log "Run:   git remote add forkrul https://github.com/forkrul/vendor_notebooklm-py.git"
  exit 1
fi

# Safety: working tree must be clean.
if [[ -n "$(git status --porcelain)" ]]; then
  log "ERROR: working tree is dirty. Commit or stash first."
  git status --short >&2
  exit 1
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)
if [[ "$current_branch" != "main" ]]; then
  log "WARN: not on 'main' (currently on '$current_branch'). Continuing."
fi

log "Fetching origin (read-only) …"
if (( DRY_RUN )); then
  log "[dry-run] would: git fetch origin --tags --prune"
else
  git fetch origin --tags --prune
fi

ahead=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "?")
log "origin/main is $ahead commits ahead of local main."
if [[ "$ahead" == "0" ]]; then
  log "Already up to date."
  exit 0
fi

log "Rebasing local main onto origin/main …"
if (( DRY_RUN )); then
  log "[dry-run] would: git rebase origin/main"
  log "[dry-run] would: git push forkrul main --tags"
  exit 0
fi

git rebase origin/main

log "Pushing to forkrul …"
git push forkrul main
git push forkrul --tags

log "Done. Local main is at $(git rev-parse --short HEAD)."
