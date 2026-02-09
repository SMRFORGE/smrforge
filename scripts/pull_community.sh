#!/bin/bash
# Pull Community changes into Pro repo (merge public/main into current branch).
# Run from smrforge-pro. Requires 'public' remote: git remote add public https://github.com/SMRFORGE/smrforge.git
# Usage: ./scripts/pull_community.sh

set -e
cd "$(dirname "$0")/.."

git remote | grep -q public || {
  echo "Add public remote first: git remote add public https://github.com/SMRFORGE/smrforge.git" >&2
  exit 1
}
git fetch public
git merge public/main -m "Merge community changes from public/main"
