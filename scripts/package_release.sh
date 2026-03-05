#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VERSION="$(tr -d ' \n\r' < VERSION)"
STAMP="$(date +%Y%m%d-%H%M%S)"
PACKAGE_BASE="entitlement-schema-v${VERSION}"
WORK_DIR="dist/${PACKAGE_BASE}"
ARCHIVE_PATH="dist/${PACKAGE_BASE}.tar.gz"
CHECKSUM_PATH="${ARCHIVE_PATH}.sha256"
MANIFEST_PATH="dist/${PACKAGE_BASE}.manifest.txt"

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"
mkdir -p dist

cp -R README.md LICENSE VERSION \
  demo graph_database llm python_model relational_database resource secret unittest \
  __init__.py system_config.example.ini \
  "$WORK_DIR"/

find "$WORK_DIR" -name "__pycache__" -type d -prune -exec rm -rf {} +
find "$WORK_DIR" -name ".DS_Store" -type f -delete
find "$WORK_DIR" -name "*.pyc" -type f -delete

tar -czf "$ARCHIVE_PATH" -C dist "$PACKAGE_BASE"
shasum -a 256 "$ARCHIVE_PATH" > "$CHECKSUM_PATH"

{
  echo "Package: ${PACKAGE_BASE}"
  echo "Version: ${VERSION}"
  echo "Created: ${STAMP}"
  echo "Archive: ${ARCHIVE_PATH}"
  echo "Checksum: ${CHECKSUM_PATH}"
  echo
  echo "Included files:"
  find "$WORK_DIR" -type f | sed "s|^$WORK_DIR/||" | sort
} > "$MANIFEST_PATH"

echo "Release package created:"
echo "  $ARCHIVE_PATH"
echo "  $CHECKSUM_PATH"
echo "  $MANIFEST_PATH"
