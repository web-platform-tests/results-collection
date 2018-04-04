# Copyright 2018 The WPT Dashboard Project. All rights reserved.

# Use of this source code is governed by a BSD-style license
# that can be found in the LICENSE file.

# Run this script in cron, and have it write to the
# /var/www/html folder a file called sha
#
# You should have Options +Includes, mod_include and XBitHack on in
# your <VirtualHost> for the htdocs/index.html page to work.

sha="$(git ls-remote https://github.com/w3c/web-platform-tests.git | head -1 | cut -f 1)"

echo "${sha}"
