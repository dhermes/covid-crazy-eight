# `covid-crazy-eight`

> Bare Bones Webapp to Play Crazy Eights with friends while quarantines

To run

```
DEBUG=true PLAYERS=Joe,Eve,Tim python src/app.py
```

I'll probably cut a lot of corners while making this. To build and run in
Docker

```
docker build --tag dhermes/covid-crazy-eight:latest --file Dockerfile .
docker run \
  --rm \
  --interactive \
  --tty \
  --env DEBUG=true \
  --env PLAYERS=Joe,Eve,Tim \
  --publish 15071:15071 \
  dhermes/covid-crazy-eight:latest
```

To deploy to Google Cloud Run:

```
gcloud auth login                          # Make sure logged in
gcloud auth list                           # Double check logged in account
gcloud projects list                       # Pick a project
PROJECT_ID="<project_id>"                  # Use PROJECT_ID (not name or number)
gcloud config set project "${PROJECT_ID}"  # Set PROJECT_ID
# Use Google Cloud Build to build the image
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/covid-crazy-eight:latest"
# Deploy to Google Cloud Run
gcloud run deploy \
  --image "gcr.io/${PROJECT_ID}/covid-crazy-eight" \
  --set-env-vars '^:^PLAYERS=Larry,Sergey,Sundar' \
  --port 15071 \
  --max-instances 1 \
  --allow-unauthenticated \
  --region us-west1 \
  --platform managed \
  covid-crazy-eight
# Clean up after the game has ended
gcloud run services delete \
  --region us-west1 \
  --platform managed \
  covid-crazy-eight
# Clean up container after you're really extra super done
gcloud container images list
gcloud container images delete "gcr.io/${PROJECT_ID}/covid-crazy-eight:latest"
# Look for (and delete) old builds that are still hanging around
gcloud container images list-tags "gcr.io/${PROJECT_ID}/covid-crazy-eight"
gcloud container images delete "gcr.io/${PROJECT_ID}/covid-crazy-eight@sha256:${DIGEST}"
# Consider deleting logs from Cloud Build runs
gsutil ls "gs://${PROJECT_ID}_cloudbuild/"
gsutil ls "gs://${PROJECT_ID}_cloudbuild/source/"
```
