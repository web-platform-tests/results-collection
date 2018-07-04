#!/bin/bash

if [ \( "$1" = "-h" \) -o \( "$1" = "--help" \) ]; then
  echo Usage: $(basename $0) SENTINEL_FILE >&2
  echo If SENTINEL_FILE exists, delete it and reboot the system.
  exit
fi

sentinel_file=$1

if [ -f $sentinel_file ]; then
  rm $sentinel_file
  reboot
fi
