#!/bin/bash -e

export BROWSER=
export FLAGS=--total-chunks=100

if [ -f "/root/browser-is-running.txt" ]; then
    echo "Not running, browser tests are running"
else

    # removes temporary files from browsers

    rm -rf /tmp/*mozrunner
    find /tmp -type f -name "*hromium*" -print0 | xargs -0 -r rm -f
    find /tmp -type f -name "*hrome*" -print0 | xargs -0 -r rm -f
    
    touch /root/browser-is-running.txt

    #    rm -rf ~/wptdbuild/*
    cd /root/wptdashboard/ && ./run/run.py $BROWSER $FLAGS  2>&1 | tee browser-`date +%s`.log

    rm /root/browser-is-running.txt

fi


exit 0
