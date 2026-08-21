#!/usr/bin/env bash
#
# Mixed deliberately: some invocations are plain Kubernetes verbs that port to kubectl,
# others are OpenShift-only verbs whose INTENT has to be re-expressed. A run that reports
# a flat count without that split has under-answered OPS-Q6.
set -euo pipefail

NS=payments-prod

# Portable: these map 1:1 to kubectl
oc get pods -n "$NS"
oc apply -f manifests/CONTROL-portable.yaml -n "$NS"
oc rollout status deployment/payments-notifier -n "$NS"

# OpenShift-only: no kubectl equivalent, intent must be rebuilt
oc login --token="$OC_TOKEN" --server=https://api.ocp-prod.example.internal:6443
oc project "$NS"
oc start-build payments-api --follow --wait
oc rollout latest dc/payments-api
oc process -f manifests/openshift-build.yaml -p WORKER_REPLICAS=4 | oc apply -f -
oc set triggers dc/payments-api --from-image=payments-api:latest -c payments-api
oc get route payments-api -o jsonpath='{.spec.host}'
oc adm policy add-scc-to-user anyuid -z payments-api -n "$NS"

echo "deployed"
