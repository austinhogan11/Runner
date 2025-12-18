Overview

This repo now contains:
- GitHub Actions workflow that builds/pushes images to ACR and bumps the dev Helm values file with the new image tags.
- Argo CD Application manifest that syncs the Helm chart (using values-dev.yaml) into the cluster, enabling a one‑command, repeatable dev deploy.

Paths
- Workflow: .github/workflows/build-and-push.yaml
- Chart: projects/Runner/deploy/helm/runner/
- Dev values: projects/Runner/deploy/helm/runner/values-dev.yaml
- Argo CD app: projects/Runner/deploy/argocd/runner-dev-app.yaml

Prereqs
- AKS + ACR already provisioned; AKS kubelet has AcrPull.
- Ingress-NGINX installed in cluster (for public access).
- GitHub OIDC to Azure configured and the following repo secrets set:
  - AZURE_CLIENT_ID
  - AZURE_TENANT_ID
  - AZURE_SUBSCRIPTION_ID
  - ACR_LOGIN_SERVER (e.g., runneracrdev.azurecr.io)

Local smoke deploy (single command)
- helm upgrade --install runner deploy/helm/runner -n runner -f projects/Runner/deploy/helm/runner/values-dev.yaml --wait

CI flow
1) On push to main, the workflow logs into Azure and ACR.
2) Builds backend and frontend as linux/amd64, pushes to ACR tagged with the commit SHA.
3) Updates values-dev.yaml to use the new tags and commits that change.
4) If Argo CD watches this repo/path, it will auto-sync and roll out.

Argo CD setup
1) Install Argo CD in the cluster (argocd namespace).
2) Edit projects/Runner/deploy/argocd/runner-dev-app.yaml and set repoURL to this repo.
3) Apply: kubectl -n argocd apply -f projects/Runner/deploy/argocd/runner-dev-app.yaml
4) Argo CD will create/maintain resources in namespace runner using values-dev.yaml.

Notes
- Avoid --reuse-values with Helm; rely on the values-dev.yaml to prevent type drift.
- Frontend is built with VITE_API_URL=/api and Ingress routes / to frontend, /api to backend with regex + rewrite.

Strava (Phase 1)
- Create a secret with your Strava app creds and redirect URL:
  kubectl -n runner create secret generic runner-strava \
    --from-literal=STRAVA_CLIENT_ID=<id> \
    --from-literal=STRAVA_CLIENT_SECRET=<secret> \
    --from-literal=STRAVA_REDIRECT_URI=http://runner.chosenrunning.com/api/strava/callback

- In values-dev.yaml add:
  backend:
    extraEnvFromSecrets:
      - runner-strava

- Optional daily sync (last 24h):
  stravaSync:
    enabled: true
    schedule: "0 9 * * *"  # 09:00 UTC

The CronJob calls the in-cluster backend URL:
http://<release>-runner-backend.runner.svc.cluster.local/api/strava/sync?weeks=1

