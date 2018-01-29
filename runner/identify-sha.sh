# Copyright 2018 The WPT Dashboard Project. All rights reserved.

# Use of this source code is governed by a BSD-style license
# that can be found in the LICENSE file.

# Run this script in cron, and have it write to the
# /var/www/html folder a file called sha

sha="$(git ls-remote https://github.com/w3c/web-platform-tests.git | head -1 | cut -f 1 | cut -c 1-10)"

echo "${sha}"

