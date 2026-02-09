#!/bin/bash
# Push current branch to origin (Pro private repo).
# Usage: ./scripts/push_pro.sh [-m "commit msg"]  # commit first if -m
#        ./scripts/push_pro.sh                     # push only

set -e
cd "$(dirname "$0")/.."

MSG=""
while getopts m: opt; do
  case $opt in m) MSG="$OPTARG";; esac
done

if [ -n "$MSG" ]; then
  git add -A
  [ -z "$(git status --porcelain)" ] || git commit -m "$MSG"
fi
branch=$(git rev-parse --abbrev-ref HEAD)
git push -u origin "$branch"
