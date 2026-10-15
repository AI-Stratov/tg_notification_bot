#!/bin/sh
# Print the CHANGELOG.md section for a version: release-notes.sh 1.1.0
# Fails if the section is missing or empty.
set -eu

version="$1"
notes=$(awk -v version="$version" '
    /^## / { if (found) exit; found = ($2 == version); next }
    found
' CHANGELOG.md)

if [ -z "$(printf '%s' "$notes" | tr -d '[:space:]')" ]; then
    echo "CHANGELOG.md has no section for $version" >&2
    exit 1
fi
printf '%s\n' "$notes"
