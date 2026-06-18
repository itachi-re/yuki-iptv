#!/usr/bin/env bash
set -Eeuo pipefail

[[ -e debian ]] && {
    echo "debian already exists"
    exit 1
}

ln -s build/debian debian
trap 'rm -f debian' EXIT

dpkg-buildpackage -uc -b
