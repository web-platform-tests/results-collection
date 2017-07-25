# Deployment

The site is hosted on App Engine.

## Credential management

No public-facing routes require authentication. There is only one route that requires credentials: `POST /test-runs`, for uploading a new test run.

You can set environment variables with the command `gcloud -E TESTRUN_UPLOAD_SECRET:0xthesecret`.
