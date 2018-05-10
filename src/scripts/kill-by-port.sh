#!/bin/bash

port=$1

if [ "$port" == "" ]; then
  echo Usage: $(readlink -f $0) PORT
  echo Kill process bound to the TCP/IP PORT if any such process exists.
  exit 1
fi

pid=$(netstat -nlp 2>/dev/null | \
  grep :$port | \
  sed 's/^.*LISTEN\s*\([0-9]\+\).*/\1/')


if [ "$pid" == "" ]; then
  echo No process bound to port $port >&2
  exit 0
fi

echo $pid | grep '^[0-9]\+$' > /dev/null

if [ $? != '0' ]; then
  echo Unable to kill process bound to $port >&2
  exit 1
fi

kill -9 $pid > /dev/null 2> /dev/null

if [ $? == '0' ]; then
  echo Killed process $pid
else
  echo Unable to kill process $pid >&2
  exit 1
fi
