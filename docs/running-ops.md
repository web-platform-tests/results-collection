# Running Operations Documentation

## Push a new Docker image to the registry

You must be logged into the `wptdashboard` project in `gcloud`. Be advised
this is risky as all Jenkins builds pull and use this container.

```sh
LOCAL_NAME=wptd-testrun-jenkins
IMAGE_NAME=gcr.io/wptdashboard/$LOCAL_NAME

docker build -t $LOCAL_NAME -f Dockerfile.jenkins .
docker tag $LOCAL_NAME $IMAGE_NAME
gcloud docker -- push $IMAGE_NAME
```
