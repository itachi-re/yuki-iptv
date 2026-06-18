#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$(realpath "$0")")/.." || exit 1

[[ -e debian ]] && {
    echo "debian already exists"
    exit 1
}

ln -s build/debian debian
trap 'rm -f debian' EXIT

dpkg-buildpackage -uc -b
