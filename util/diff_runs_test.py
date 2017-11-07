import argparse
import logging
import mock
import unittest

from diff_runs import Fetcher, RunDiffer, PlatformsAtRevision


class DiffRunTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_args = mock.Mock(spec=argparse.Namespace)
        self.mock_fetcher = mock.Mock(spec=Fetcher)
        self.mock_logger = mock.Mock(spec=logging.Logger)

        self.differ = RunDiffer(
            self.mock_args, self.mock_logger, self.mock_fetcher)

    def test_fetch_failure(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")
        self.mock_fetcher.fetchResults.return_value = None

        self.differ.diff()

        self.mock_logger.warning.assert_called()
        self.mock_logger.info.assert_not_called()

    def test_no_difference(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")
        self.mock_fetcher.fetchResults.return_value = {
            '/mock/path.html': [1, 1],
            '/mock/path_2.html': [3, 5],
        }

        self.differ.diff()

        logged = self.mock_logger.info.call_args[0][0]
        self.assertIn('0 differences', logged)
        self.assertIn('2 tests', logged)

    def test_one_difference(self):
        self.mock_args.after = PlatformsAtRevision.parse("chrome@latest")
        self.mock_args.before = PlatformsAtRevision.parse("chrome@0123456789")

        def results(sha, platform):
            if sha == 'latest':
                return {
                    '/mock/path.html': [0, 1]
                }
            if sha == '0123456789':
                return {
                    '/mock/path.html': [1, 1]
                }
        self.mock_fetcher.fetchResults.side_effect = results

        self.differ.diff()

        logged = self.mock_logger.info.call_args[0][0]
        self.assertIn('1 differences', logged)
        self.assertIn('1 tests', logged)


if __name__ == '__main__':
    unittest.main()
