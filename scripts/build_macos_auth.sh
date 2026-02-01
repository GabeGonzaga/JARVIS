#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/bin"
SRC="$ROOT/native/macos_auth/TouchIDAuth.swift"

mkdir -p "$OUT"
xcrun swiftc "$SRC" -o "$OUT/jarvis-auth"
echo "Built $OUT/jarvis-auth"
