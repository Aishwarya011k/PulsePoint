#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME=pulsepoint
echo "Deleting kind cluster '${CLUSTER_NAME}'..."
kind delete cluster --name "${CLUSTER_NAME}" || true
echo "Done."
