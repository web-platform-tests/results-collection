# This replaces run/run.py
import os

from runner import Runner


def main(runner):
    runner.run()


if __name__ == '__main__':
    main(Runner(
        # For making instance-internal network requests for metadata.
        # See:
        # https://cloud.google.com/compute/docs/storing-retrieving-metadata
        metadata_url='http://metadata.google.internal/computeMetadata/v1',
        prod_host='https://wptdashboard.appspot.com',
        gs_results_bucket='wptd',
        prod_run=bool(os.environ.get('PROD_RUN', False)),
        prod_wet_run=bool(os.environ.get('PROD_WET_RUN', False)),
        sha=os.environ.get('WPT_SHA'),
        sauce_from_metadata=bool(os.environ.get('SAUCE_FROM_METADATA', False)),
        sauce_key=os.environ.get('SAUCE_KEY', ''),
        sauce_user=os.environ.get('SAUCE_USER', ''),
        wpt_path=(os.environ.get('WPT_PATH') or
                  '%s/web-platform-tests' % (os.environ.get('HOME'))),
        wptd_path=(os.environ.get('WPTD_PATH') or
                   '%s/wptdashboard' % (os.environ.get('HOME'))),
        output_path=(os.environ.get('WPTD_OUT_PATH') or
                     '%s/wptdout' % (os.environ.get('HOME'))),
        run_path=os.environ.get('RUN_PATH', ''),
    ))
