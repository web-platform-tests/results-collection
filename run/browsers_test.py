import unittest
import json
import os
import re


VALID_PLATFORM_ID_REGEX = r"^[a-z0-9\-\.]+$"
REQUIRED_PLATFORM_FIELDS = {
    'currently_run': (True, False),
    'initially_loaded': (True, False),
    'browser_name': ('chrome', 'firefox', 'edge'),
    'browser_version': None,
    'os_name': ('linux', 'windows'),
    'os_version': None,
}

class TestBrowsers(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestBrowsers, self).__init__(*args, **kwargs)
        filepath = os.path.join(os.path.dirname(__file__), os.pardir, 'browsers.json')
        with open(filepath) as f:
            self.browsers = json.load(f)

    def test_all_platforms_have_only_valid_characters(self):
        for platform_id, platform_info in self.browsers.iteritems():
            self.assertTrue(re.match(VALID_PLATFORM_ID_REGEX, platform_id),
                'platform_id with invalid characters: %s' % platform_id)

    def test_all_browsers_have_required_fields(self):
        for platform_id, platform_info in self.browsers.iteritems():
            for key, valid_values in REQUIRED_PLATFORM_FIELDS.iteritems():
                self.assertTrue(key in platform_info.keys(),
                    'Required field missing: %s (platform %s)' % (key, platform_id))

                if REQUIRED_PLATFORM_FIELDS[key] != None:
                    self.assertTrue(platform_info[key] in REQUIRED_PLATFORM_FIELDS[key],
                        'Field has invalid value: %s (platform %s)' % (key, platform_id))

    def test_no_two_browser_configs_are_equal(self):
        for first_platform_id, first_platform in self.browsers.iteritems():
            identical_platforms = [
                second_platform for second_platform_id, second_platform
                in self.browsers.iteritems()
                if second_platform == first_platform
            ]
            self.assertEqual(len(identical_platforms), 1,
                'Duplicate platforms detected: %s' % identical_platforms)


if __name__ == '__main__':
    unittest.main()
