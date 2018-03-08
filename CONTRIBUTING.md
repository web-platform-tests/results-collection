# Wpt.fyi - Guidelines for Contributors
Thank you for your interest in the Web Platform Tests Dashboard! You can participate by reporting issues and/or submitting bugs or new features via Pull Reques. (If you’d like to help maintain the project, please see our Maintainers’ Guidelines as well.)
 
Here are a few guidelines to help you get started.

## Filing Issues
If something is not working as you would expect, before filing an issue, make sure you read [our documentation](https://github.com/w3c/wptdashboard/blob/master/README.md). 
 
If you can’t find what you are looking for in the documentation, we recommend you join our IRC channel and tell us there about the problem you are having. 
 
If you can’t find what you are looking for either in our documentation or in our [IRC channel](http://irc.w3.org/?channels=testing), or if you want to report a bug, the best way to have it addressed is by [filing an issue](https://github.com/w3c/wptdashboard/issues/new).
 
Before you create a new issue, please [search the wptdashboard repository](https://github.com/w3c/wptdashboard/issues) to see if any existing issues address the same problem you are having.  If you find a matching issue but have further detail to add, please leave a comment on the issue.

### Creating an Issue
Issues should be created to report bugs or propose new features. The content we expect depends on the kind of issue.

1. If it’s about a bug, it should contain: 
-  Web browser and operating system in use
-  Steps to reproduce it
-  Expected Results
-  Actual Results (screenshot if applicable)

2. If it’s about a feature, it should contain:
-  Use case or problem statement
-  Summary of the desired functionality

### Review
Issues will receive review and comment within 3 business days.

## Submitting Pull Requests 
When you have been working on fixing a bug or adding a new feature and your code is ready to be reviewed, you should [file a pull request](https://github.com/w3c/wptdashboard/compare).

### Creation 
Pull requests should be focused on a specific issue, feature or bug. The smaller the scope, and the less scope mixing, the better. This makes it easier to review and merge your changes.

A Pull Request will either be merged or rejected. In order to enable us to successfully merge your pull request, please provide the following:

1. Link to the issue
-  This could be incorporated in the title or in the description

2. Write a useful description and title
-  Make sure your PR’s title is accurate and specific
-  Write a detailed description explaining what your code accomplishes, and why this work is taking place (what problem is it solving, or what feature is it adding and why?).
-  A pull request that contains only a link to an ad-hoc staging url will not be merged.  Please describe in detail what your PR does, so that it can be accurately reviewed.

3. Include relevant review information 
-  Provide explicit instructions for how to run the code (if necessary)
-  Highlight the files that have changed and group them into concepts, or issues being solved
-  Be sure that any special configurations, environment requirements, or dependencies are clearly identified for reviewers

4. Other information
-  If your patch changes any functionality, it must include automated tests that verify the expected behavior.
-  Make sure to @mention anyone who should review your pull request, and clarify what you want them to review and why

### Review
Pull Requests will be reviewed and commented within 3 business days. There is no guaranteed time box for pull requests to be closed with or without merge; however, a best effort will be given to do so in a reasonable time frame.

## Code of Conduct

The [wpt.fyi](https://github.com/w3c/wptdashboard) project is dedicated to providing a harassment-free experience for everyone, regardless of gender, sexual orientation, disability, age, physical appearance, body size, race, or religion. Sexual language and imagery is not appropriate. We do not tolerate harassment in any form and we are committed to partnering with you to foster a healthy collaboration environment. 

See the details of our policy here: [Code of Conduct](https://github.com/w3c/wptdashboard/blob/master/CODE_OF_CONDUCT.md).
