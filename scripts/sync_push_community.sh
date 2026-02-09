#!/bin/bash
# Sync Community content to public repo and push.
# Run from smrforge-pro (private) repo. Requires sync_to_public.py in scripts/.
# Usage: ./scripts/sync_push_community.sh [--dry-run] [--no-push] [--public-repo /path/to/smrforge]

set -e
cd "$(dirname "$0")/.."
repo_root=$(pwd)
script_dir="$(dirname "$0")"

DRY_RUN=""
NO_PUSH=""
PUBLIC_REPO=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)   DRY_RUN="--dry-run"; shift ;;
    --no-push)   NO_PUSH=1; shift ;;
    --public-repo) PUBLIC_REPO="$2"; shift 2 ;;
    *) shift ;;
  esac
done

[ -f scripts/sync_to_public.py ] || { echo "sync_to_public.py not found. Run from smrforge-pro repo." >&2; exit 1; }

python scripts/pre_sync_check.py || exit $?
python scripts/sync_to_public.py --skip-leakage-check $DRY_RUN ${PUBLIC_REPO:+--public-repo "$PUBLIC_REPO"} || exit $?

[ -n "$DRY_RUN" ] && exit 0

if [ -z "$PUBLIC_REPO" ]; then
  if [[ "$repo_root" == *smrforge-pro* ]]; then
    PUBLIC_REPO="$(dirname "$repo_root")/smrforge"
  else
    PUBLIC_REPO="$(dirname "$repo_root")/smrforge-public"
  fi
fi
[ -d "$PUBLIC_REPO/.git" ] || { echo "Public repo not found at $PUBLIC_REPO" >&2; exit 1; }

if [ -z "$NO_PUSH" ]; then
  ( cd "$PUBLIC_REPO"
    git checkout -B community-sync 2>/dev/null || true
    git add -A
    [ -z "$(git status --porcelain)" ] || git commit -m "Community sync from smrforge-pro"
    git push -u origin community-sync
  )
else
  echo "Skipping push (--no-push). Next: cd $PUBLIC_REPO; git add -A; git commit -m 'Community sync'; git push origin community-sync"
fi
