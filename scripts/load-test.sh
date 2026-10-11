#!/usr/bin/env bash
# Simple CPU load generator used to demonstrate HPA autoscaling in the demo.
set -euo pipefail

URL="${URL:-http://clinicflow.local/api/appointments}"
REQUESTS="${REQUESTS:-2000}"

echo "Sending ${REQUESTS} requests to ${URL} ..."
for i in $(seq 1 "${REQUESTS}"); do
  curl -s "$URL" >/dev/null || true
done
echo "Load test completed - check 'kubectl get hpa -n clinicflow'"
