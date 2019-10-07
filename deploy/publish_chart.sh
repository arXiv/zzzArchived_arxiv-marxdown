#!/bin/bash

# Add S3 repo. Requires AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be set
# in the environment.
helm plugin install https://github.com/hypnoglow/helm-s3.git || echo "Helm S3 already installed"
helm repo add arxiv $HELM_REPOSITORY
helm repo update
echo "Updated Helm repo"

helm package deploy/marxdown
helm s3 push ./marxdown-*.tgz arxiv || echo "This chart version already published"