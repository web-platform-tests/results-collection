# wpt.fyi: Guidelines for Maintainers

Thank you for your interest in helping maintain the WPT Dashboard! Here are the Pull Request and Issues guidelines and policies for Maintainers of the project:

## Moderating Discussion

Guidelines for issue reports and pull requests are included in this project’s `CONTRIBUTING.md` file. Ensure that contributors honor these recommendations. Close discussions in any of the following events:

1. The main description of the issue is no longer what is/was intended
  - If the description is inaccurate or describes something other than what is discussed in the issue, the issue should be closed.

2. The comment thread of an issue gets too long and contains more than just additions and clarifications.
  - The issue is no longer relevant or it has been resolved.
  - The issue is a request that is deemed “out of scope” for the project.
  - The issue contains content that violates the [Code of Conduct](CODE_OF_CONDUCT.md).

## Managing Results Data

*Note: A new results reporting system is under development, so the following instructions are subject to change.*

In order to improve throughput and limit the impact of intermittent failure, this project subdivides the task of collecting web-platform-tests results. It does this by using the "chunking" functionality of the WPT CLI, splitting the entire test suite into a number of segments and executing the segments in parallel. Once all segments are complete, the build master consolidates the results, uploads them to a central storage location, and notifies a database server of the new data.

Although the system is designed to detect incomplete results and abort the upload process, unexpected errors may allow such invalid datasets to be reported. In this event, maintainers should take the following actions:

1. Create an issue in this project's issue tracker to describe the error
2. Update the database record describing the faulty dataset by modifying the
   `BrowserName` field according to the following pattern:

       invalid-{{browser name}}-{{issue reference}}

   For instance, to annotate an invalid data set for the "experimental" version of the Firefox browser, referencing issue 345 on GitHub.com, the `BrowserName` filed should be renamed to:

       invalid-firefox-experimental-gh-345

## Reviewing Pull Requests

Maintainers should review and post comments on pull requests within 3 business days. There is no guaranteed time box for pull requests to be closed with or without merge; however, make an effort to do so in a reasonable time frame.

## Reverting Patches

If you find a patch causes [wpt.fyi](http://wpt.fyi) to no longer function as intended, revert it immediately. Leave a comment detailing what happened as a result of the PR, and work with the contributor to resolve the problem and try again.


## Code of Conduct

The [wpt.fyi](https://github.com/w3c/wptdashboard) project is dedicated to providing a harassment-free experience for everyone, regardless of gender, sexual orientation, disability, age, physical appearance, body size, race, or religion. Sexual language and imagery is not appropriate. We do not tolerate harassment in any form and we are committed to partnering with you to foster a healthy collaboration environment.

See the details of our policy here: [Code of Conduct](https://github.com/w3c/wptdashboard/blob/master/CODE_OF_CONDUCT.md).
