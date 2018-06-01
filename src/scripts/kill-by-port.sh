#!/bin/bash

port=$1

if [ "$port" == "" ]; then
  echo Usage: $(readlink -f $0) PORT
  echo Kill process bound to the TCP/IP PORT if any such process exists.
  exit 1
fi

# Prefer `lsof` over `netstat` for portability between GNU and BSD
# implementations
pid=$(lsof -n -i :$port | \
  grep LISTEN | \
  awk '{ print $2 }')


if [ "$pid" == "" ]; then
  echo The current user is not running a process bound to port $port >&2
  exit 0
fi

kill -9 $pid > /dev/null 2> /dev/null

if [ $? == '0' ]; then
  echo Killed process $pid
else
  echo Unable to kill process $pid >&2
  exit 1
fi
