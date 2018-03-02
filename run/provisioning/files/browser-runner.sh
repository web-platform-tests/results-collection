#!/bin/bash -e

. /home/{{application_user}}/.bash_profile

export BROWSER={{browser}}

if [ -f "./browser-is-running.txt" ]; then
    echo "Not running, browser tests are running"
else

    # removes temporary files from browsers

    rm -rf /tmp/*mozrunner
    find /tmp -type f -name "*hromium*" -print0 | xargs -0 -r rm -f
    find /tmp -type f -name "*hrome*" -print0 | xargs -0 -r rm -f
    
    touch ./browser-is-running.txt

    #    rm -rf ~/wptdbuild/*
    cd ./wptdashboard/ && ./run/run.py $BROWSER \
      --partial-threshold 98 \
      --upload --create-testrun --total-chunks 100 2>&1 | \
        tee browser-`date +%s`.log

    rm ./browser-is-running.txt

fi


exit 0
