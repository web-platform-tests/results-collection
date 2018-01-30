#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

sha=$(curl curl --silent --output /dev/null https://sha.wpt.fyi/sha)
echo "Fetching repo at commit SHA $sha..."
stamp=$(date +'%s')
git clone https://github.com/w3c/web-platform-tests.git ~/tests-$stamp &> /dev/null
cd ~/tests-$stamp
git checkout $sha &> /dev/null
echo "Finding good tests..."
mkdir ~/tests-$stamp/__wptd__working__/

(
    find * -maxdepth 0 -type d;
    find css/* -maxdepth 0 -type d
) | grep -vE '^(common|css|css/fonts|css/reference|css/support|css/vendor-imports|fonts|interfaces|media)$' | while read d; do
    if [[ -f "$d/OWNERS" ]]; then
	if [[ -f "~/tests-$stamp/__wptd__working__/$d.tgz" ]]; then
	    rm ~/tests-$stamp/__wptd__working__/$d.tgz 
	fi
	echo "Bundling $d tests..."
        tar zcf ~/tests-$stamp/__wptd__working__/$d.tgz $d &> /dev/null
        continue
    fi
    #grep -qF 'file://' "$d/OWNERS" && continue
    #grep -qF '# TEAM: ' "$d/OWNERS" || echo "Missing TEAM: $d"
    #grep -qF '# COMPONENT: ' "$d/OWNERS" || echo "Missing COMPONENT: $d"
done
