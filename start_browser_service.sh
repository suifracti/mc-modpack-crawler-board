#!/bin/sh
set -u

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
cd "$SCRIPT_DIR" || exit 1

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Node.js and npm are required. Install Node.js LTS, then run this launcher again."
  printf "Press Return to close... "
  read -r _
  exit 1
fi

echo "[1/2] Building the browser dashboard..."
if ! npm --prefix apps/web run build:desktop; then
  echo "The browser dashboard could not be built."
  printf "Press Return to close... "
  read -r _
  exit 1
fi

echo "[2/2] Starting the local browser service..."
echo "Close this terminal window to stop the service."
npm --prefix apps/desktop start
EXIT_CODE=$?
echo ""
echo "Browser service stopped with exit code $EXIT_CODE."
printf "Press Return to close... "
read -r _
exit "$EXIT_CODE"
