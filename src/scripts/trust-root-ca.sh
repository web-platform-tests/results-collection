#!/bin/bash

function help {
  echo Usage: $(basename $0) CA_CERTIFICATE >&2
  echo Import a trusted root certificate authority on a macOS system >&2
}

if [ "$1" == "-h" ]; then
  help
  exit 0
fi

if [ ! -f "$1" ]; then
  help
  exit 1
fi

common_name=$(sed -n -e 's/.*CN=//p' $1 | head -n 1)

if [ "$common_name" == "" ]; then
  echo Could not detect common name from file $1. >&2
  exit 1
fi

echo Deleting any existing certificate for common name \"$common_name\"

security delete-certificate -c $common_name

echo Adding certificate

security add-trusted-cert \
  -d \
  -r trustRoot \
  -k /Library/Keychains/System.keychain \
  $1
