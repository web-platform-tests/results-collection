# wpt.fyi: Guidelines for Contributors

Thank you for your interest in the Web Platform Tests Dashboard! You can participate by reporting [Issues](https://github.com/w3c/wptdashboard/issues/new) and/or submitting bugs or new features via [Pull Request](https://github.com/w3c/wptdashboard/compare). (If you'd like to help maintain the project, please see the [Maintainers' Guidelines](MAINTAINERS.md) as well.)
 
Here are a few guidelines to help you get started.

## Filing Issues

If something is not working as you would expect, before filing an issue, make sure you read [the documentation](https://github.com/w3c/wptdashboard/blob/master/README.md). 
 
If you can't find what you are looking for in the documentation, we recommend that you join [irc.w3.org#testing](http://irc.w3.org/?channels=testing) and start a discussion about the problem you are having. 
 
If you can't find what you are looking for either in [the documentation](https://github.com/w3c/wptdashboard/blob/master/README.md) or in [irc.w3.org#testing](http://irc.w3.org/?channels=testing), please file a [detailed issue](https://github.com/w3c/wptdashboard/issues/new).
 
Before creating a new issue, please [search the existing issues for any existing discussions](https://github.com/w3c/wptdashboard/issues) that may be relevant. If you find a matching issue but have further detail to add, please leave a comment on the issue.

### Creating an Issue

Issues should be created to report bugs or propose new features. The content  expected depends on the kind of issue.

1. Bug reports should contain: 
  - Web browser and operating system in use
  - Steps to reproduce it
  - Expected Results
  - Actual Results (screenshot if applicable)

2. Feature requests should contain:
  - Use case or problem statement
  - Summary of the desired functionality

### Review

Issues will be triaged within 3 business days.

## Pull Requests 

When you have been working on fixing a bug or adding a new feature and your code is ready to be reviewed, you should [file a pull request](https://github.com/w3c/wptdashboard/compare).

### Creating a Pull Request

Pull Requests should be focused on a specific issue, feature or bug. The smaller the scope, the better. This makes it easier to review and merge your changes. Patches should be reasonably focused on addressing a single [issue](https://github.com/w3c/wptdashboard/issues). 

A Pull Request will either be accepted or rejected. In order to enable us to successfully merge your pull request, please provide the following:

1. Link to and reference an issue
  - This could be incorporated in the title or in the description
  - Use of Github annotations in commit messages is encouraged, for example:
    +  "%Commit message%, Fixes gh-XX" or "%Commit message%, Fixes #XX"
    +  "%Commit message%, Closes gh-XX" or "%Commit message%, Closes #XX"
    +  "%Commit message%, Addresses gh-XX" or "%Commit message%, Addresses #XX"

2. Write a useful description and title
  - Make sure your PR's title is accurate and specific
  - Write a detailed description in the "Leave a comment" box explaining what your code accomplishes, and why this work is taking place (what problem is it solving, or what feature is it adding and why?).
    + There should be a reference to a relevant issue.
    + Optionally, a link to a staging url
      * When including a link, please also include any relevant instructions for reviewing and running the code locally (see below). 

3. Include relevant review information 
  - Provide explicit instructions for how to run the code (if necessary)
  - Highlight the files that have changed and group them into concepts, or issues being solved
  - Be sure that any special configurations, environment requirements, or dependencies are clearly identified for reviewers.
    + This may include, but is not limited to: 
      * Python, Go or JavaScript dependencies
      * Data (mock or otherwise) dependencies
      * Secrets required to run the code
      * Environment Variables

4. Other information
  - If your patch changes any functionality, it must include automated tests that verify the expected behavior.
  - Make sure to @mention anyone who should review your pull request, and clarify what you want them to review and why

5. Ensure that patch passes all CI testing requirements and is "Green"; otherwise please include an explanation of the failure. 

### Review

Pull Requests will receive review and response within 3 business days. There is no guaranteed time box for pull requests to be closed with or without merge; however, a best effort will be given to do so in a reasonable time frame.

## Code of Conduct

The [wpt.fyi](https://github.com/w3c/wptdashboard) project is dedicated to providing a harassment-free experience for everyone, regardless of gender, sexual orientation, disability, age, physical appearance, body size, race, or religion. Sexual language and imagery is not appropriate. We do not tolerate harassment in any form and we are committed to partnering with you to foster a healthy collaboration environment. 

See the details of our policy here: [Code of Conduct](CODE_OF_CONDUCT.md).
